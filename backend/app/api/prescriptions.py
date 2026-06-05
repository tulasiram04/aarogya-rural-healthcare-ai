import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.agents.graph import compiled_aarogya_agent
from app.services.data_filter import get_portal_patient_ids

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])

@router.post("/upload", response_model=dict)
async def upload_prescription(
    patient_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an image of a handwritten prescription for OCR processing.
    Triggers the LangGraph agent to extract medicines and auto-generate compliance schedules.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified patient does not exist."
        )

    # Validate image format
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG/PNG image uploads are supported."
        )

    image_bytes = await file.read()
    
    # Initialize LangGraph AgentState inputs
    state_input = {
        "patient_id": patient.id,
        "telegram_id": patient.telegram_id,
        "input_type": "prescription",
        "raw_input_bytes": image_bytes,
        "raw_input_text": None,
        "preferred_language": patient.preferred_language,
        "extracted_data": {},
        "symptom_answers": {},
        "risk_level": "low",
        "risk_message": None,
        "chat_history": [],
        "response_english": "",
        "response_translated": "",
        "response_audio_bytes": None
    }

    try:
        # Invoke compiled LangGraph engine
        output_state = compiled_aarogya_agent.invoke(state_input)
        
        return {
            "prescription_id": output_state.get("extracted_data", {}).get("prescription_id"),
            "extracted_medicines": output_state.get("extracted_data", {}).get("medicines", []),
            "response": output_state.get("response_english"),
            "risk_assessment": {
                "risk_level": output_state.get("risk_level"),
                "risk_message": output_state.get("risk_message")
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LangGraph execution failed during prescription OCR: {str(e)}"
        )


from app.models.medical import Prescription

@router.get("", response_model=list)
def list_prescriptions(
    data_filter: str = Query("real", regex="^(all|real|demo)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient_ids = get_portal_patient_ids(db, data_filter, current_user)
    if not patient_ids:
        return []

    prescriptions = (
        db.query(Prescription)
        .filter(Prescription.patient_id.in_(patient_ids))
        .order_by(Prescription.created_at.desc())
        .all()
    )
    result = []
    for rx in prescriptions:
        result.append({
            "id": str(rx.id),
            "patient_id": str(rx.patient_id),
            "patient_name": rx.patient.full_name,
            "uploaded_at": rx.created_at.isoformat() if rx.created_at else None,
            "raw_image_url": rx.raw_image_url,
            "raw_ocr_text": rx.raw_ocr_text,
            "structured_data": rx.structured_data,
            "issue_date": rx.issue_date.isoformat() if rx.issue_date else None,
            "telegram_id": rx.telegram_id,
            "diagnosis": rx.diagnosis
        })
    return result

@router.get("/{patient_id}", response_model=list)
def list_patient_prescriptions(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    query = db.query(Prescription).filter(Prescription.patient_id == patient_id)
    prescriptions = query.order_by(Prescription.created_at.desc()).all()
    result = []
    for rx in prescriptions:
        result.append({
            "id": str(rx.id),
            "patient_id": str(rx.patient_id),
            "patient_name": rx.patient.full_name,
            "uploaded_at": rx.created_at.isoformat() if rx.created_at else None,
            "raw_image_url": rx.raw_image_url,
            "raw_ocr_text": rx.raw_ocr_text,
            "structured_data": rx.structured_data,
            "issue_date": rx.issue_date.isoformat() if rx.issue_date else None,
            "telegram_id": rx.telegram_id,
            "diagnosis": rx.diagnosis
        })
    return result
