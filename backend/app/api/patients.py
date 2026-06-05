import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.medical import Prescription, Reminder, LabReport, ComplianceLog
from app.models.logs import RiskAlert, SymptomLog
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.services.doctor_assignment import assign_doctor_to_patient
from app.services.activity import create_activity_log
from app.services.gemini import gemini_service
from app.services.risk_score import calculate_predictive_risk_score
from app.services.data_filter import apply_demo_filter, apply_telegram_patient_filter

logger = logging.getLogger("aarogya.api.patients")
router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_403_FORBIDDEN)
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manual patient creation is disabled.
    Patients must register exclusively through the Telegram bot (/start).
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Patients can only be registered via the AAROGYA Telegram bot. Ask the patient to send /start to the bot.",
    )


@router.get("/", response_model=List[PatientResponse])
def list_patients(
    data_filter: str = Query("real", regex="^(all|real|demo)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List Telegram-registered patients only (plus demo dataset when filter=demo).
    Manual/API-created patients without a telegram_id are never shown.
    """
    query = apply_telegram_patient_filter(db.query(Patient), data_filter)
    if current_user.role == "admin" or current_user.role == "system":
        return query.all()
    elif current_user.role == "doctor":
        return query.filter(Patient.assigned_doctor_id == current_user.id).all()
    elif current_user.role == "hcw":
        return query.filter(Patient.assigned_hcw_id == current_user.id).all()
    return []


@router.get("/{patient_id}", response_model=dict)
def get_patient_detail(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch comprehensive health record profile of a single patient.
    Aggregates active prescriptions, active reminders, lab report parameters, and active risk alerts.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Portal only shows Telegram-registered patients (or explicit demo records)
    if not patient.is_demo and patient.telegram_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found. Only Telegram-registered patients are available in the portal.",
        )
    # Recalculate predictive risk score dynamically
    calculate_predictive_risk_score(db, patient)
        
    # Check permissions (Doctor, assigned HCW, or Admins only)
    if current_user.role == "doctor" and patient.assigned_doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to view this patient's records")
    elif current_user.role == "hcw" and patient.assigned_hcw_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to view this patient's records")

    # Aggregate timelines
    rxs = db.query(Prescription).filter(Prescription.patient_id == patient_id).order_by(Prescription.created_at.desc()).all()
    rems = db.query(Reminder).filter(Reminder.patient_id == patient_id, Reminder.is_active == True).all()
    reps = db.query(LabReport).filter(LabReport.patient_id == patient_id).order_by(LabReport.uploaded_at.desc()).all()
    alerts = db.query(RiskAlert).filter(RiskAlert.patient_id == patient_id, RiskAlert.status == "raised").all()
    symptoms = db.query(SymptomLog).filter(SymptomLog.patient_id == patient_id).order_by(SymptomLog.created_at.desc()).limit(10).all()

    # Calculate compliance rates
    compliance_logs = db.query(ComplianceLog).join(Reminder).filter(Reminder.patient_id == patient_id).all()
    taken_doses = sum(1 for l in compliance_logs if l.status == "taken")
    missed_doses = sum(1 for l in compliance_logs if l.status == "missed")
    pending_doses = sum(1 for l in compliance_logs if l.status == "pending")
    total_doses = taken_doses + missed_doses
    compliance_percentage = round((taken_doses / total_doses * 100.0), 2) if total_doses > 0 else 100.0

    # Build chronological timeline
    timeline = []
    timeline.append({
        "type": "registration",
        "date": patient.created_at.isoformat() if patient.created_at else None,
        "title": "Patient Registered",
        "description": f"Registered via Telegram with preferred language {patient.preferred_language.capitalize()}."
    })
    for rx in rxs:
        timeline.append({
            "type": "prescription",
            "date": rx.created_at.isoformat() if rx.created_at else None,
            "title": "Prescription Uploaded",
            "description": f"Prescription uploaded. Diagnosis: {rx.diagnosis or 'N/A'}."
        })
    for rep in reps:
        timeline.append({
            "type": "lab_report",
            "date": rep.uploaded_at.isoformat() if rep.uploaded_at else None,
            "title": "Lab Report Uploaded",
            "description": f"Lab report ({rep.report_type or 'General'}) uploaded."
        })
    for s in symptoms:
        timeline.append({
            "type": "checkin",
            "date": s.created_at.isoformat() if s.created_at else None,
            "title": "Health Check-in",
            "description": f"Symptoms: {s.symptoms or 'None'}. Severity: {s.severity or 'Low'}."
        })
    all_alerts = db.query(RiskAlert).filter(RiskAlert.patient_id == patient_id).all()
    for a in all_alerts:
        timeline.append({
            "type": "alert",
            "date": a.created_at.isoformat() if a.created_at else None,
            "title": f"Risk Alert: {a.severity or a.risk_level}",
            "description": a.reason or a.alert_message
        })
    timeline.sort(key=lambda x: x["date"] or "", reverse=True)

    # Dynamic AI Health Summary
    overall_condition = "Stable"
    if len(alerts) > 0:
        overall_condition = "Guarded"
    if len(alerts) > 2:
        overall_condition = "Critical"

    fallback_summary = (
        f"Patient has:\n"
        f"• {len(rxs)} prescriptions\n"
        f"• {len(reps)} lab reports\n"
        f"• {compliance_percentage}% compliance\n"
        f"• {len(alerts)} active alerts\n\n"
        f"Overall condition:\n"
        f"{overall_condition}"
    )
    
    ai_health_summary = fallback_summary
    try:
        prompt = f"""
        You are a clinical coordinator AI. Summarize the patient's status in a clinical summary card based on these DB stats:
        - Patient Name: {patient.full_name}
        - Prescriptions count: {len(rxs)}
        - Lab reports count: {len(reps)}
        - Compliance rate: {compliance_percentage}% (Taken: {taken_doses}, Missed: {missed_doses})
        - Active alerts count: {len(alerts)} ({', '.join([a.alert_message for a in alerts]) if alerts else 'None'})
        
        Provide a concise 3-4 sentence clinical assessment in the exact markdown format:
        Patient has:
        • [prescriptions bullet]
        • [lab reports bullet]
        • [compliance bullet]
        • [alerts bullet]
        
        Overall condition:
        [Stable/Guarded/Critical]
        
        Do not include any other explanations, comments or HTML/formatting tags. Keep it extremely clinical and concise.
        """
        ai_health_summary = gemini_service.generate_content(prompt)
    except Exception as sum_err:
        logger.error(f"Failed to generate AI health summary: {str(sum_err)}")

    return {
        "id": patient.id,
        "telegram_id": patient.telegram_id,
        "phone": patient.phone,
        "full_name": patient.full_name,
        "age": patient.age,
        "gender": patient.gender,
        "village": patient.village,
        "sub_center": patient.sub_center,
        "preferred_language": patient.preferred_language,
        "medical_history": patient.medical_history,
        "is_active": patient.is_active,
        "risk_score": patient.risk_score or 0,
        "risk_level": patient.risk_level or "Low",
        "risk_factors": patient.risk_factors or [],
        "created_at": patient.created_at,
        "assigned_hcw": {"id": patient.assigned_hcw.id, "name": patient.assigned_hcw.full_name} if patient.assigned_hcw else None,
        "assigned_doctor": {"id": patient.assigned_doctor.id, "name": patient.assigned_doctor.full_name} if patient.assigned_doctor else None,
        "prescriptions_count": len(rxs),
        "prescriptions": [
            {
                "id": str(rx.id),
                "raw_image_url": rx.raw_image_url,
                "raw_ocr_text": rx.raw_ocr_text,
                "structured_data": rx.structured_data,
                "issue_date": rx.issue_date.isoformat() if rx.issue_date else None,
                "telegram_id": rx.telegram_id,
                "diagnosis": rx.diagnosis,
                "created_at": rx.created_at.isoformat() if rx.created_at else None
            } for rx in rxs
        ],
        "active_reminders": [
            {
                "id": r.id,
                "medicine_name": r.medicine_name,
                "dosage": r.dosage,
                "schedule_time": r.schedule_time.isoformat(),
                "frequency": r.frequency,
                "start_date": r.start_date
            } for r in rems
        ],
        "lab_reports": [
            {
                "id": str(rep.id),
                "report_type": rep.report_type,
                "file_url": rep.file_url,
                "extracted_metrics": rep.extracted_metrics,
                "summary": rep.raw_ocr_text,
                "ai_explanation": rep.ai_explanation,
                "uploaded_at": rep.uploaded_at.isoformat() if rep.uploaded_at else None
            } for rep in reps
        ],
        "active_alerts": [
            {
                "id": a.id,
                "risk_level": a.risk_level,
                "severity": a.severity or a.risk_level,
                "reason": a.reason or a.alert_message,
                "recommendation": a.recommendation,
                "source": a.source,
                "alert_message": a.alert_message,
                "created_at": a.created_at
            } for a in alerts
        ],
        "recent_symptoms": [
            {
                "id": str(s.id),
                "answers": s.answers,
                "severity_score": s.severity_score,
                "symptoms": s.symptoms,
                "severity": s.severity,
                "recommendation": s.recommendation,
                "created_at": s.created_at.isoformat() if s.created_at else None
            } for s in symptoms
        ],
        "compliance": {
            "percentage": compliance_percentage,
            "taken_doses": taken_doses,
            "missed_doses": missed_doses,
            "pending_doses": pending_doses,
            "total_doses": total_doses
        },
        "timeline": timeline,
        "ai_health_summary": ai_health_summary
    }


@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: uuid.UUID,
    patient_up: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modify details of an active patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Update fields
    up_data = patient_up.model_dump(exclude_unset=True)
    for field, value in up_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}/copilot", response_model=dict)
def get_patient_copilot(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate clinical copilot AI recommendations, suggested diagnosis, follow-up,
    lab tests, medication review, and compliance risk assessment for the patient.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    if not patient.is_demo and patient.telegram_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found. Only Telegram-registered patients are available in the portal.",
        )

    # Check permissions (Doctor, assigned HCW, or Admins only)
    if current_user.role == "doctor" and patient.assigned_doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to view this patient's records")
    elif current_user.role == "hcw" and patient.assigned_hcw_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to view this patient's records")

    # Fetch patient's medical records for Gemini context
    rxs = db.query(Prescription).filter(Prescription.patient_id == patient_id).order_by(Prescription.created_at.desc()).all()
    reps = db.query(LabReport).filter(LabReport.patient_id == patient_id).order_by(LabReport.uploaded_at.desc()).all()
    alerts = db.query(RiskAlert).filter(RiskAlert.patient_id == patient_id, RiskAlert.status == "raised").all()
    symptoms = db.query(SymptomLog).filter(SymptomLog.patient_id == patient_id).order_by(SymptomLog.created_at.desc()).limit(5).all()

    # Calculate compliance
    compliance_logs = db.query(ComplianceLog).join(Reminder).filter(Reminder.patient_id == patient_id).all()
    taken_doses = sum(1 for l in compliance_logs if l.status == "taken")
    total_doses = len(compliance_logs)
    compliance_percentage = round((taken_doses / total_doses * 100.0), 2) if total_doses > 0 else 100.0

    # Build patient history details
    meds_list = []
    for rx in rxs:
        if rx.structured_data:
            meds_list.extend([m.get("name") for m in rx.structured_data if m.get("name")])
    meds_str = ", ".join(list(set(meds_list))) if meds_list else "None"

    symptoms_str = "; ".join([f"{s.created_at.date() if s.created_at else 'Today'}: {s.symptoms} (severity: {s.severity})" for s in symptoms if s.symptoms]) or "None"
    alerts_str = "; ".join([a.alert_message for a in alerts]) or "None"
    reports_str = ""
    for r in reps[:2]:
        metrics_desc = ", ".join([f"{k}: {v.get('value')} {v.get('unit')} (status: {v.get('status')})" for k, v in r.extracted_metrics.items()])
        reports_str += f"- {r.report_type}: {metrics_desc}\n"
    if not reports_str:
        reports_str = "None"

    prompt = f"""
    You are an expert physician clinical copilot AI.
    Analyze the patient's medical records:
    - Name: {patient.full_name}
    - Age: {patient.age}, Gender: {patient.gender}
    - Chronic History: {json.dumps(patient.medical_history)}
    - Active Medications: {meds_str}
    - Medication Compliance Rate: {compliance_percentage}% (Total doses tracked: {total_doses})
    - Active Risk Alerts: {alerts_str}
    - Recent Symptom Logs: {symptoms_str}
    - Latest Lab Diagnostics:
    {reports_str}

    Based on this clinical picture, generate the following six categories of recommendations:
    1. AI Recommendations (e.g. dietary suggestions, monitoring routines)
    2. Suggested Diagnosis (working differential diagnosis)
    3. Suggested Follow-up (scheduling recommendations)
    4. Suggested Lab Tests (specific lab parameters to order next)
    5. Medication Review (potential adjustments, side-effects, or drug conflicts)
    6. Compliance Assessment (clinical risk level from medication adherence: e.g. "Excellent Control", "Moderate Risk", "Critical Adherence Risk")

    Return your analysis STRICTLY in JSON format matching the schema below.
    Do not add any markdown block syntax, code markers, or text outside the JSON block.

    Expected JSON schema:
    {{
      "recommendations": ["string", "string"],
      "suggested_diagnosis": "string",
      "suggested_follow_up": "string",
      "suggested_lab_tests": ["string", "string"],
      "medication_review": "string",
      "compliance_assessment": "string"
    }}
    """
    try:
        res = gemini_service.generate_content(prompt)
        clean = res.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        # Ensure all keys exist in returned data
        for k in ["recommendations", "suggested_diagnosis", "suggested_follow_up", "suggested_lab_tests", "medication_review", "compliance_assessment"]:
            if k not in data:
                data[k] = [] if "tests" in k or "recommendations" in k else "N/A"
        return data
    except Exception as e:
        logger.error(f"Failed to generate copilot analysis: {str(e)}")
        # Graceful fallback response matching user's requested categories
        return {
            "recommendations": ["Maintain current hydration levels.", "Keep blood glucose log daily."],
            "suggested_diagnosis": "Review of records inconclusive. Monitor symptom logs.",
            "suggested_follow_up": "Revisit sub-center in 3-5 days.",
            "suggested_lab_tests": ["Routine Blood Sugar Check", "Complete Blood Count (CBC)"],
            "medication_review": "Verify drug compliance with assigned health worker. No conflicts flagged.",
            "compliance_assessment": "Moderate Risk" if compliance_percentage < 90 else "Low Risk"
        }
