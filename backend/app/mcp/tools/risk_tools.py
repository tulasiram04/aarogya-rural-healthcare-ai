"""
MCP Tools — Patient risk assessment retrieval.
"""
import logging
from app.core.database import SessionLocal
from app.models.patient import Patient

logger = logging.getLogger("aarogya.mcp.tools.risk")


def get_patient_risk(patient_id: str) -> dict:
    """
    Retrieve the current risk score and risk level for a patient.

    Returns the predictive risk assessment including risk factors
    computed by the AAROGYA risk engine.
    """
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return {"error": f"Patient with id '{patient_id}' not found."}

        risk_score = patient.risk_score or 0
        risk_level = patient.risk_level or "Low"

        # Normalize risk_level display
        level_map = {
            "low": "Low",
            "medium": "Medium",
            "moderate": "Medium",
            "high": "High",
            "critical": "Critical",
        }
        display_level = level_map.get(risk_level.lower(), risk_level.title())

        return {
            "patient_id": str(patient.id),
            "patient_name": patient.full_name,
            "risk_score": risk_score,
            "risk_level": display_level,
            "risk_factors": patient.risk_factors or [],
        }
    except Exception as e:
        logger.error(f"get_patient_risk failed: {e}")
        return {"error": f"Failed to retrieve patient risk: {str(e)}"}
    finally:
        db.close()
