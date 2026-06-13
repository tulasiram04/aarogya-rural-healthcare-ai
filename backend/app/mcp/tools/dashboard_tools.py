"""
MCP Tools — Dashboard summary and recent alerts.
"""
import logging
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.medical import Prescription, Reminder, ComplianceLog
from app.models.logs import RiskAlert

logger = logging.getLogger("aarogya.mcp.tools.dashboard")


def get_dashboard_summary() -> dict:
    """
    Retrieve a high-level dashboard summary of the entire AAROGYA platform.

    Returns aggregate counts of patients, active alerts, prescriptions,
    and the overall village health score (average medication compliance).
    """
    db = SessionLocal()
    try:
        total_patients = db.query(func.count(Patient.id)).scalar() or 0
        active_alerts = (
            db.query(func.count(RiskAlert.id))
            .filter(RiskAlert.status == "raised")
            .scalar() or 0
        )
        total_prescriptions = db.query(func.count(Prescription.id)).scalar() or 0

        # Compute village health score as overall medication compliance rate
        compliance_logs = db.query(ComplianceLog).join(Reminder).all()
        total_logs = len(compliance_logs)
        taken_logs = sum(1 for log in compliance_logs if log.status == "taken")
        village_health_score = round(
            (taken_logs / total_logs) * 100.0 if total_logs > 0 else 0.0, 1
        )

        return {
            "patients": total_patients,
            "alerts": active_alerts,
            "prescriptions": total_prescriptions,
            "village_health_score": village_health_score,
        }
    except Exception as e:
        logger.error(f"get_dashboard_summary failed: {e}")
        return {"error": f"Failed to retrieve dashboard summary: {str(e)}"}
    finally:
        db.close()


def get_recent_alerts() -> dict:
    """
    Retrieve the most recent active risk alerts across all patients.

    Returns up to 20 unresolved alerts sorted by creation date,
    including patient names and risk severity information.
    """
    db = SessionLocal()
    try:
        alerts = (
            db.query(RiskAlert)
            .filter(RiskAlert.status == "raised")
            .order_by(RiskAlert.created_at.desc())
            .limit(20)
            .all()
        )

        alert_list = []
        for a in alerts:
            patient = db.query(Patient).filter(Patient.id == a.patient_id).first()
            alert_list.append({
                "id": str(a.id),
                "patient_id": str(a.patient_id),
                "patient_name": patient.full_name if patient else "Unknown",
                "risk_level": a.risk_level,
                "severity": a.severity or a.risk_level,
                "alert_message": a.alert_message,
                "reason": a.reason,
                "recommendation": a.recommendation,
                "source": a.source,
                "created_at": str(a.created_at),
            })

        return {"alerts": alert_list}
    except Exception as e:
        logger.error(f"get_recent_alerts failed: {e}")
        return {"error": f"Failed to retrieve recent alerts: {str(e)}"}
    finally:
        db.close()
