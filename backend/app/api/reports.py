import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.agents.graph import compiled_aarogya_agent
from app.services.data_filter import get_portal_patient_ids

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/upload", response_model=dict)
async def upload_report(
    patient_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an image of a lab test report.
    Triggers the LangGraph agent to extract biomarker values, flag high ranges, and draft a simplified explanation.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified patient does not exist."
        )

    # Validate file format (can be image or PDF, but for OCR we check standard image types here)
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "application/pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG/PNG images or PDF reports are supported."
        )

    file_bytes = await file.read()
    
    # Initialize LangGraph AgentState inputs
    state_input = {
        "patient_id": patient.id,
        "telegram_id": patient.telegram_id,
        "input_type": "report",
        "raw_input_bytes": file_bytes,
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
            "report_id": output_state.get("extracted_data", {}).get("report_id"),
            "extracted_metrics": output_state.get("extracted_data", {}).get("metrics", {}),
            "summary_english": output_state.get("response_english"),
            "summary_translated": output_state.get("response_translated"),
            "risk_assessment": {
                "risk_level": output_state.get("risk_level"),
                "risk_message": output_state.get("risk_message")
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LangGraph execution failed during lab report extraction: {str(e)}"
        )


from app.models.medical import LabReport

@router.get("", response_model=list)
def list_reports(
    data_filter: str = Query("real", regex="^(all|real|demo)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient_ids = get_portal_patient_ids(db, data_filter, current_user)
    if not patient_ids:
        return []

    reports = (
        db.query(LabReport)
        .filter(LabReport.patient_id.in_(patient_ids))
        .order_by(LabReport.uploaded_at.desc())
        .all()
    )
    result = []
    for lr in reports:
        result.append({
            "id": str(lr.id),
            "patient_id": str(lr.patient_id),
            "patient_name": lr.patient.full_name,
            "uploaded_at": lr.uploaded_at.isoformat() if lr.uploaded_at else None,
            "file_url": lr.file_url,
            "report_type": lr.report_type,
            "raw_ocr_text": lr.raw_ocr_text,
            "extracted_metrics": lr.extracted_metrics,
            "summary_local_lang": lr.summary_local_lang,
            "ai_explanation": lr.ai_explanation
        })
    return result

@router.get("/{patient_id}", response_model=list)
def list_patient_reports(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    query = db.query(LabReport).filter(LabReport.patient_id == patient_id)
    reports = query.order_by(LabReport.uploaded_at.desc()).all()
    result = []
    for lr in reports:
        result.append({
            "id": str(lr.id),
            "patient_id": str(lr.patient_id),
            "patient_name": lr.patient.full_name,
            "uploaded_at": lr.uploaded_at.isoformat() if lr.uploaded_at else None,
            "file_url": lr.file_url,
            "report_type": lr.report_type,
            "raw_ocr_text": lr.raw_ocr_text,
            "extracted_metrics": lr.extracted_metrics,
            "summary_local_lang": lr.summary_local_lang,
            "ai_explanation": lr.ai_explanation
        })
    return result
