"""
MCP Tools — Patient prescription retrieval.
"""
import logging
from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.medical import Prescription

logger = logging.getLogger("aarogya.mcp.tools.prescription")


def get_patient_prescriptions(patient_id: str) -> dict:
    """
    Retrieve all prescriptions for a given patient.

    Returns the list of prescriptions with diagnosis details,
    structured medication data, and dates.
    """
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return {"error": f"Patient with id '{patient_id}' not found."}

        prescriptions = (
            db.query(Prescription)
            .filter(Prescription.patient_id == patient_id)
            .order_by(Prescription.created_at.desc())
            .all()
        )

        rx_list = []
        for rx in prescriptions:
            rx_list.append({
                "id": str(rx.id),
                "diagnosis": rx.diagnosis or "N/A",
                "medicines": rx.structured_data or [],
                "issue_date": str(rx.issue_date) if rx.issue_date else None,
                "created_at": str(rx.created_at),
            })

        return {
            "patient_id": str(patient.id),
            "patient_name": patient.full_name,
            "total_prescriptions": len(rx_list),
            "prescriptions": rx_list,
        }
    except Exception as e:
        logger.error(f"get_patient_prescriptions failed: {e}")
        return {"error": f"Failed to retrieve prescriptions: {str(e)}"}
    finally:
        db.close()
