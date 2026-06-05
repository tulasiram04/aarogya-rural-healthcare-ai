import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.medical import Reminder, ComplianceLog
from app.schemas.medical import ReminderResponse, ComplianceLogResponse, ComplianceLogUpdate

router = APIRouter(prefix="/reminders", tags=["reminders"])

@router.get("/patient/{patient_id}", response_model=List[ReminderResponse])
def get_patient_reminders(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all active medicine reminders registered for a specific patient."""
    reminders = db.query(Reminder).filter(
        Reminder.patient_id == patient_id, 
        Reminder.is_active == True
    ).all()
    return reminders


@router.post("/compliance/{log_id}", response_model=ComplianceLogResponse)
def log_reminder_compliance(
    log_id: uuid.UUID,
    compliance_update: ComplianceLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Log patient response for a specific medication schedule event.
    Marks log as 'taken' or 'missed' and updates completion timestamp.
    """
    log = db.query(ComplianceLog).filter(ComplianceLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance log entry not found."
        )

    log.status = compliance_update.status
    log.taken_time = compliance_update.taken_time or datetime.now(timezone.utc)
    if compliance_update.response_voice_url:
        log.response_voice_url = compliance_update.response_voice_url
        
    db.commit()
    db.refresh(log)
    return log


@router.get("/compliance/stats/{patient_id}", response_model=dict)
def get_compliance_stats(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate medicine compliance rates (taken vs missed) for the Doctor Dashboard.
    Returns percentages and timelines.
    """
    logs = db.query(ComplianceLog).join(Reminder).filter(
        Reminder.patient_id == patient_id
    ).all()

    total = len(logs)
    if total == 0:
        return {"compliance_rate": 100.0, "total_events": 0, "taken": 0, "missed": 0, "pending": 0}

    taken = sum(1 for l in logs if l.status == "taken")
    missed = sum(1 for l in logs if l.status == "missed")
    pending = sum(1 for l in logs if l.status == "pending")

    rate = (taken / (total - pending)) * 100.0 if (total - pending) > 0 else 100.0

    return {
        "compliance_rate": round(rate, 2),
        "total_events": total,
        "taken": taken,
        "missed": missed,
        "pending": pending
    }
