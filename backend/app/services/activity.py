import logging
from sqlalchemy.orm import Session
from app.models.logs import ActivityLog

logger = logging.getLogger("aarogya.activity")

def create_activity_log(
    db: Session,
    patient_id: str,
    activity_type: str,
    message: str,
    is_demo: bool = False,
) -> None:
    """
    Creates an activity log entry for a patient.
    """
    try:
        activity = ActivityLog(
            patient_id=patient_id,
            activity_type=activity_type,
            message=message,
            is_demo=is_demo,
        )
        db.add(activity)
        db.commit()
        logger.info(f"Activity logged: [{activity_type}] - {message}")
    except Exception as e:
        logger.error(f"Failed to write activity log: {str(e)}")
        db.rollback()
