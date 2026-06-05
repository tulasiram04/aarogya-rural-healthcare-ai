from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.logs import RiskAlert, SymptomLog, ActivityLog
from app.models.medical import ComplianceLog, Reminder, Prescription, LabReport
from app.services.data_filter import apply_demo_filter, apply_telegram_patient_filter
from app.services.demo_data import delete_demo_records, purge_all_mock_patients

logger = logging.getLogger("aarogya.dashboard")

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _filter_patients_by_role(query, current_user: User):
    if current_user.role == "doctor":
        return query.filter(Patient.assigned_doctor_id == current_user.id)
    if current_user.role == "hcw":
        return query.filter(Patient.assigned_hcw_id == current_user.id)
    return query


@router.get("/summary", response_model=dict)
def get_dashboard_summary(
    data_filter: str = Query("real", regex="^(all|real|demo)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch consolidated metrics for dashboard visualization."""
    try:
        patient_query = apply_telegram_patient_filter(db.query(Patient), data_filter)
        patient_query = _filter_patients_by_role(patient_query, current_user)

        patient_ids = [p.id for p in patient_query.all()]

        alert_query = db.query(RiskAlert).filter(RiskAlert.status == "raised")
        alert_query = apply_demo_filter(alert_query, RiskAlert, data_filter)
        if patient_ids:
            alert_query = alert_query.filter(RiskAlert.patient_id.in_(patient_ids))
        elif current_user.role in ("doctor", "hcw"):
            alert_query = alert_query.filter(False)

        rx_query = apply_demo_filter(db.query(Prescription), Prescription, data_filter)
        lr_query = apply_demo_filter(db.query(LabReport), LabReport, data_filter)
        if patient_ids:
            rx_query = rx_query.filter(Prescription.patient_id.in_(patient_ids))
            lr_query = lr_query.filter(LabReport.patient_id.in_(patient_ids))
        elif current_user.role in ("doctor", "hcw"):
            rx_query = rx_query.filter(False)
            lr_query = lr_query.filter(False)

        total_patients = len(patient_ids)
        active_patients = patient_query.filter(Patient.is_active == True).count()  # noqa: E712
        active_alerts = alert_query.count()
        critical_alerts = alert_query.filter(RiskAlert.risk_level == "critical").count()
        prescriptions_uploaded = rx_query.count()
        lab_reports_uploaded = lr_query.count()

        if patient_ids:
            compliance_logs = db.query(ComplianceLog).join(Reminder).filter(
                Reminder.patient_id.in_(patient_ids)
            ).all()
            total_logs = len(compliance_logs)
            taken_logs = sum(1 for l in compliance_logs if l.status == "taken")
            compliance_rate = (taken_logs / total_logs) * 100.0 if total_logs > 0 else 0.0
        else:
            compliance_rate = 0.0

        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        new_prescriptions = rx_query.filter(Prescription.created_at >= one_day_ago).count()
        new_reports = lr_query.filter(LabReport.uploaded_at >= one_day_ago).count()

        village_stats = []
        if patient_ids:
            villages = db.query(Patient.village, func.count(Patient.id)).filter(
                Patient.id.in_(patient_ids)
            ).group_by(Patient.village).all()

            for vil_name, count in villages:
                if not vil_name:
                    continue
                v_patient_ids = [p.id for p in patient_query.filter(Patient.village == vil_name).all()]
                v_logs = db.query(ComplianceLog).join(Reminder).filter(
                    Reminder.patient_id.in_(v_patient_ids)
                ).all()
                v_total = len(v_logs)
                v_taken = sum(1 for l in v_logs if l.status == "taken")
                v_rate = (v_taken / v_total) * 100.0 if v_total > 0 else 0.0
                village_stats.append({
                    "village": vil_name,
                    "patient_count": count,
                    "compliance_rate": round(v_rate, 2),
                })

        village_health_score = 0.0
        if village_stats:
            village_health_score = round(
                sum(v["compliance_rate"] for v in village_stats) / len(village_stats), 1
            )

        all_patients = patient_query.all()
        disease_counts = {}
        for p in all_patients:
            if isinstance(p.medical_history, dict):
                for k, v in p.medical_history.items():
                    if v and v not in [False, "no", "None"]:
                        name = k.replace("_", " ").title()
                        disease_counts[name] = disease_counts.get(name, 0) + 1

        all_prescriptions = rx_query.all()
        for rx in all_prescriptions:
            if rx.diagnosis and rx.diagnosis.lower() not in ["n/a", "none", "unknown", "unknown diagnosis"]:
                diag = rx.diagnosis.strip().title()
                disease_counts[diag] = disease_counts.get(diag, 0) + 1

        top_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_diseases_list = [{"name": d, "count": c} for d, c in top_diseases]

        village_risk_query = db.query(Patient.village, func.count(RiskAlert.id)).join(
            RiskAlert, RiskAlert.patient_id == Patient.id
        ).filter(RiskAlert.status == "raised")
        village_risk_query = apply_demo_filter(village_risk_query, RiskAlert, data_filter)
        if patient_ids:
            village_risk_query = village_risk_query.filter(Patient.id.in_(patient_ids))
        top_risk_villages = village_risk_query.group_by(Patient.village).order_by(
            func.count(RiskAlert.id).desc()
        ).limit(5).all()
        top_risk_villages_list = [
            {"village": v or "Unknown", "alert_count": c} for v, c in top_risk_villages
        ]

        active_patient_query = db.query(Patient.full_name, func.count(SymptomLog.id)).join(
            SymptomLog, SymptomLog.patient_id == Patient.id
        )
        active_patient_query = apply_demo_filter(active_patient_query, SymptomLog, data_filter)
        if patient_ids:
            active_patient_query = active_patient_query.filter(Patient.id.in_(patient_ids))
        most_active_patients = active_patient_query.group_by(Patient.id, Patient.full_name).order_by(
            func.count(SymptomLog.id).desc()
        ).limit(5).all()
        most_active_list = [{"name": p, "check_ins": c} for p, c in most_active_patients]

        missed_meds_query = db.query(Reminder.medicine_name, func.count(ComplianceLog.id)).join(
            ComplianceLog, ComplianceLog.reminder_id == Reminder.id
        ).filter(ComplianceLog.status == "missed")
        if patient_ids:
            missed_meds_query = missed_meds_query.filter(Reminder.patient_id.in_(patient_ids))
        most_missed_meds = missed_meds_query.group_by(Reminder.medicine_name).order_by(
            func.count(ComplianceLog.id).desc()
        ).limit(5).all()
        most_missed_list = [{"medicine": m, "missed_count": c} for m, c in most_missed_meds]

        patients_attention = []
        for p in all_patients:
            if (p.risk_score or 0) >= 61 or p.risk_level in ("High", "Critical", "high", "critical"):
                patients_attention.append({
                    "id": str(p.id),
                    "name": p.full_name,
                    "village": p.village,
                    "risk_score": p.risk_score or 0,
                    "risk_level": p.risk_level or "Moderate",
                })
        patients_attention.sort(key=lambda x: x["risk_score"], reverse=True)
        patients_attention = patients_attention[:5]

        ai_summary = None
        if total_patients > 0:
            try:
                from app.services.gemini import gemini_service
                prompt = f"""
                You are the chief AI medical health officer for AAROGYA Rural Health.
                Analyze these aggregated sub-center parameters:
                - Total Patients: {total_patients}
                - Overall Medication Compliance Rate: {compliance_rate:.1f}%
                - Active Risk Alerts: {active_alerts} (Critical: {critical_alerts})
                - Village Health Score: {village_health_score}%
                - Top Chronic Disease Trends: {', '.join([d['name'] for d in top_diseases_list]) or 'None'}
                - Highest Risk Villages: {', '.join([v['village'] for v in top_risk_villages_list]) or 'None'}

                Write a brief 3-4 sentence clinical overview. Keep tone clinical and actionable. No markdown.
                """
                ai_summary = gemini_service.generate_content(prompt).strip()
            except Exception as gem_err:
                logger.error(f"Failed to generate village insights summary: {str(gem_err)}")
                ai_summary = (
                    f"Monitoring {total_patients} patients with {compliance_rate:.1f}% adherence. "
                    f"{active_alerts} active alerts require review."
                )

        return {
            "total_patients": total_patients,
            "active_patients": active_patients,
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
            "prescriptions_uploaded": prescriptions_uploaded,
            "lab_reports_uploaded": lab_reports_uploaded,
            "risk_alerts": active_alerts,
            "overall_compliance": round(compliance_rate, 2),
            "village_health_score": village_health_score,
            "new_prescriptions": new_prescriptions,
            "new_reports": new_reports,
            "village_analytics": village_stats,
            "village_insights": {
                "top_diseases": top_diseases_list,
                "top_risk_villages": top_risk_villages_list,
                "most_active_patients": most_active_list,
                "most_missed_medicines": most_missed_list,
                "patients_requiring_attention": patients_attention,
                "village_summary": ai_summary,
            },
            "data_filter": data_filter,
        }
    except Exception as e:
        logger.exception(f"Error generating dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/seed_demo", response_model=dict)
def load_hackathon_demo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove old demo records, preserve real data, seed fresh hackathon dataset."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only administrators can trigger Hackathon Demo Mode.",
        )
    try:
        delete_demo_records(db)
        import sys
        if "/workspace" not in sys.path:
            sys.path.insert(0, "/workspace")
        from seed_demo_data import seed  # noqa: E402
        seed()
        return {
            "status": "success",
            "message": "Hackathon demo dataset loaded! All demo records marked is_demo=true.",
        }
    except Exception as e:
        logger.exception(f"Demo seeding failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")


@router.delete("/clean_demo", response_model=dict)
def clean_demo_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete all mock/demo patients. Preserves only real Telegram-registered patients."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only administrators can clean demo data.",
        )
    try:
        counts = purge_all_mock_patients(db)
        return {
            "status": "success",
            "message": "All mock data removed. Real Telegram patients preserved.",
            "deleted": counts,
            "preserved_patients": "Telegram-bot registered patients only (telegram_id required)",
        }
    except Exception as e:
        logger.exception(f"Demo cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
