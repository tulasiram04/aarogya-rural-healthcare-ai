import logging
from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.logs import RiskAlert, SymptomLog
from app.models.medical import ComplianceLog, Reminder, LabReport

logger = logging.getLogger("aarogya.risk_score")

def calculate_predictive_risk_score(db: Session, patient: Patient) -> dict:
    """
    Calculate a clinical risk score (0-100), risk level, and contributing factors
    based on patient's symptoms, lab reports, compliance, chronic conditions, and alerts.
    """
    score = 10  # Base healthy baseline
    factors = []

    # 1. Chronic Conditions from medical_history
    history = patient.medical_history or {}
    for condition, val in history.items():
        if val and val not in [False, "no", "None"]:
            cond_name = condition.replace("_", " ").title()
            score += 10
            factors.append(f"Chronic Condition: {cond_name}")

    # 2. Compliance rate
    compliance_logs = db.query(ComplianceLog).join(Reminder).filter(Reminder.patient_id == patient.id).all()
    total_doses = len(compliance_logs)
    if total_doses > 0:
        taken_doses = sum(1 for l in compliance_logs if l.status == "taken")
        compliance_percentage = (taken_doses / total_doses) * 100.0
        if compliance_percentage < 75.0:
            score += 25
            factors.append(f"Poor Medication Adherence (Compliance: {compliance_percentage:.1f}%)")
        elif compliance_percentage < 90.0:
            score += 12
            factors.append(f"Suboptimal Medication Adherence (Compliance: {compliance_percentage:.1f}%)")
    else:
        # If no reminders set yet, check if there are active prescriptions
        pass

    # 3. Active Risk Alerts
    active_alerts = db.query(RiskAlert).filter(
        RiskAlert.patient_id == patient.id,
        RiskAlert.status == "raised"
    ).all()
    for alert in active_alerts:
        score += 20
        factors.append(f"Active Alert: {alert.reason or alert.alert_message}")

    # 4. Latest Symptom Log Severity
    latest_symptom = db.query(SymptomLog).filter(
        SymptomLog.patient_id == patient.id
    ).order_by(SymptomLog.created_at.desc()).first()
    if latest_symptom:
        if latest_symptom.severity == "High":
            score += 25
            factors.append(f"Severe Symptoms Reported Today: {latest_symptom.symptoms or 'Unknown'}")
        elif latest_symptom.severity == "Medium":
            score += 15
            factors.append(f"Moderate Symptoms Reported Today: {latest_symptom.symptoms or 'Unknown'}")

    # 5. Lab Reports (Biomarkers)
    latest_report = db.query(LabReport).filter(
        LabReport.patient_id == patient.id
    ).order_by(LabReport.uploaded_at.desc()).first()
    if latest_report and latest_report.extracted_metrics:
        metrics = latest_report.extracted_metrics
        for metric, data in metrics.items():
            if isinstance(data, dict):
                status = str(data.get("status", "")).lower()
                val = data.get("value")
                if status in ["high", "low"]:
                    score += 15
                    factors.append(f"Abnormal Biomarker: {metric} is {status.upper()} ({val})")

    # Bound the score
    score = min(max(score, 0), 100)

    # Determine risk level
    if score <= 30:
        level = "Low"
    elif score <= 60:
        level = "Moderate"
    elif score <= 80:
        level = "High"
    else:
        level = "Critical"

    # Save to database
    try:
        patient.risk_score = score
        patient.risk_level = level
        patient.risk_factors = factors
        db.commit()
        db.refresh(patient)
        logger.info(f"Recalculated Risk Score for {patient.full_name}: {score} ({level})")
    except Exception as e:
        logger.error(f"Failed to persist risk score for patient {patient.id}: {str(e)}")
        db.rollback()

    return {
        "risk_score": score,
        "risk_level": level,
        "risk_factors": factors
    }
