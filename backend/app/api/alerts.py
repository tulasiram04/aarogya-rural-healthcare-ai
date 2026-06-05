import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.logs import RiskAlert
from app.models.patient import Patient
from app.schemas.logs import RiskAlertResponse
from app.services.data_filter import get_portal_patient_ids

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/", response_model=List[dict])
def list_active_alerts(
    data_filter: str = Query("real", regex="^(all|real|demo)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List active alerts for Telegram-registered patients only."""
    patient_ids = get_portal_patient_ids(db, data_filter, current_user)
    if not patient_ids:
        return []

    alerts = (
        db.query(RiskAlert)
        .filter(RiskAlert.status == "raised", RiskAlert.patient_id.in_(patient_ids))
        .order_by(RiskAlert.created_at.desc())
        .all()
    )
    
    return [
        {
            "id": a.id,
            "patient_id": a.patient_id,
            "patient_name": a.patient.full_name,
            "village": a.patient.village,
            "sub_center": a.patient.sub_center,
            "risk_level": a.risk_level,
            "severity": a.severity or a.risk_level,
            "reason": a.reason or a.alert_message,
            "recommendation": a.recommendation,
            "source": a.source,
            "alert_message": a.alert_message,
            "created_at": a.created_at
        } for a in alerts
    ]


@router.patch("/{alert_id}/acknowledge", response_model=RiskAlertResponse)
def acknowledge_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record that a doctor or HCW has noticed a critical risk warning.
    Updates the log status to 'acknowledged'.
    """
    alert = db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk alert not found."
        )

    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    db.commit()
    db.refresh(alert)
    return alert


@router.patch("/{alert_id}/resolve", response_model=RiskAlertResponse)
def resolve_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a clinical danger warning as resolved after patient checkup or follow-up phone call.
    """
    alert = db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk alert not found."
        )

    alert.status = "resolved"
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert
