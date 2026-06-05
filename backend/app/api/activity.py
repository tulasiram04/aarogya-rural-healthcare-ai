import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.logs import ActivityLog
from app.services.data_filter import get_portal_patient_ids

router = APIRouter(prefix="/activity", tags=["activity"])

@router.get("", response_model=list)
def get_activity_feed(
    data_filter: str = Query("real", regex="^(all|real|demo)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch recent activity for Telegram-registered patients only."""
    patient_ids = get_portal_patient_ids(db, data_filter, current_user)
    if not patient_ids:
        return []

    activities = (
        db.query(ActivityLog)
        .filter(ActivityLog.patient_id.in_(patient_ids))
        .order_by(ActivityLog.created_at.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "id": str(act.id),
            "patient_id": str(act.patient_id),
            "patient_name": act.patient.full_name,
            "activity_type": act.activity_type,
            "message": act.message,
            "created_at": act.created_at.isoformat(),
        }
        for act in activities
    ]
