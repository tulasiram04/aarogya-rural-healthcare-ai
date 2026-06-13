"""
MCP Tools — Patient lookup and search.
"""
import logging
from app.core.database import SessionLocal
from app.models.patient import Patient

logger = logging.getLogger("aarogya.mcp.tools.patient")


def search_patient(patient_id: str) -> dict:
    """
    Look up a patient by their UUID.

    Returns structured patient demographics, contact info,
    and current risk assessment fields.
    """
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return {"error": f"Patient with id '{patient_id}' not found."}

        return {
            "id": str(patient.id),
            "name": patient.full_name,
            "age": patient.age,
            "gender": patient.gender,
            "phone": patient.phone,
            "village": patient.village,
            "sub_center": patient.sub_center,
            "preferred_language": patient.preferred_language,
            "risk_score": patient.risk_score or 0,
            "risk_level": patient.risk_level or "Low",
            "is_active": patient.is_active,
            "created_at": str(patient.created_at),
        }
    except Exception as e:
        logger.error(f"search_patient failed: {e}")
        return {"error": f"Failed to search patient: {str(e)}"}
    finally:
        db.close()
