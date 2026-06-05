"""Demo and mock data cleanup — preserves only Telegram-bot registered patients."""
import logging
from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.models.medical import Prescription, Reminder, ComplianceLog, LabReport
from app.models.logs import RiskAlert, SymptomLog, ChatHistory, ActivityLog

logger = logging.getLogger("aarogya.demo_data")

DEMO_TELEGRAM_ID_MIN = 100001
DEMO_TELEGRAM_ID_MAX = 100099


def _delete_patients_and_children(db: Session, patient_ids: list) -> dict:
    counts = {
        "activity_logs": 0,
        "chat_history": 0,
        "risk_alerts": 0,
        "symptom_logs": 0,
        "compliance_logs": 0,
        "reminders": 0,
        "lab_reports": 0,
        "prescriptions": 0,
        "patients": 0,
    }
    if not patient_ids:
        return counts

    counts["activity_logs"] = db.query(ActivityLog).filter(
        ActivityLog.patient_id.in_(patient_ids)
    ).delete(synchronize_session=False)
    counts["chat_history"] = db.query(ChatHistory).filter(
        ChatHistory.patient_id.in_(patient_ids)
    ).delete(synchronize_session=False)
    counts["risk_alerts"] = db.query(RiskAlert).filter(
        RiskAlert.patient_id.in_(patient_ids)
    ).delete(synchronize_session=False)
    counts["symptom_logs"] = db.query(SymptomLog).filter(
        SymptomLog.patient_id.in_(patient_ids)
    ).delete(synchronize_session=False)

    demo_reminder_ids = [
        r.id for r in db.query(Reminder.id).filter(Reminder.patient_id.in_(patient_ids)).all()
    ]
    if demo_reminder_ids:
        counts["compliance_logs"] = db.query(ComplianceLog).filter(
            ComplianceLog.reminder_id.in_(demo_reminder_ids)
        ).delete(synchronize_session=False)

    counts["reminders"] = db.query(Reminder).filter(
        Reminder.patient_id.in_(patient_ids)
    ).delete(synchronize_session=False)
    counts["lab_reports"] = db.query(LabReport).filter(
        LabReport.patient_id.in_(patient_ids)
    ).delete(synchronize_session=False)
    counts["prescriptions"] = db.query(Prescription).filter(
        Prescription.patient_id.in_(patient_ids)
    ).delete(synchronize_session=False)
    counts["patients"] = db.query(Patient).filter(
        Patient.id.in_(patient_ids)
    ).delete(synchronize_session=False)

    return counts


def _mock_patient_ids(db: Session) -> list:
    """Patients that are NOT valid Telegram-bot registrations."""
    return [
        p.id for p in db.query(Patient.id).filter(
            Patient.is_demo == True  # noqa: E712
            | Patient.telegram_id.is_(None)
            | (
                Patient.telegram_id.isnot(None)
                & (Patient.telegram_id >= DEMO_TELEGRAM_ID_MIN)
                & (Patient.telegram_id <= DEMO_TELEGRAM_ID_MAX)
            )
        ).all()
    ]


def delete_demo_records(db: Session) -> dict:
    """Delete demo-flagged records and hackathon telegram ID range patients."""
    counts = _delete_patients_and_children(db, _mock_patient_ids(db))

    counts["activity_logs"] += db.query(ActivityLog).filter(ActivityLog.is_demo == True).delete(synchronize_session=False)  # noqa: E712
    counts["risk_alerts"] += db.query(RiskAlert).filter(RiskAlert.is_demo == True).delete(synchronize_session=False)  # noqa: E712
    counts["prescriptions"] += db.query(Prescription).filter(Prescription.is_demo == True).delete(synchronize_session=False)  # noqa: E712
    counts["lab_reports"] += db.query(LabReport).filter(LabReport.is_demo == True).delete(synchronize_session=False)  # noqa: E712

    db.commit()
    logger.info(f"Demo data cleanup complete: {counts}")
    return counts


def purge_all_mock_patients(db: Session) -> dict:
    """
    Remove all non-Telegram patients. Keeps only real bot registrations
    (is_demo=False AND telegram_id IS NOT NULL, excluding hackathon ID range).
    """
    mock_ids = _mock_patient_ids(db)
    counts = _delete_patients_and_children(db, mock_ids)

    counts["activity_logs"] += db.query(ActivityLog).filter(ActivityLog.is_demo == True).delete(synchronize_session=False)  # noqa: E712
    counts["risk_alerts"] += db.query(RiskAlert).filter(RiskAlert.is_demo == True).delete(synchronize_session=False)  # noqa: E712
    counts["prescriptions"] += db.query(Prescription).filter(Prescription.is_demo == True).delete(synchronize_session=False)  # noqa: E712
    counts["lab_reports"] += db.query(LabReport).filter(LabReport.is_demo == True).delete(synchronize_session=False)  # noqa: E712

    db.commit()
    logger.info(f"Mock patient purge complete: {counts}")
    return counts
