import uuid
import base64
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.services.voice import voice_service
from app.services.gemini import gemini_service
from app.services.translation import translation_service
from app.agents.graph import compiled_aarogya_agent

router = APIRouter(prefix="/assistant", tags=["assistant"])
logger = logging.getLogger("aarogya.api.assistant")

@router.post("/voice", response_model=dict)
async def process_voice_assistant(
    file: UploadFile = File(...),
    language: str = Form("english"),
    patient_id: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process clinical voice assistant queries.
    Transcribes audio -> runs clinical analysis -> synthesizes voice response.
    """
    try:
        audio_bytes = await file.read()
        mime_type = file.content_type or "audio/ogg"
        
        db_patient = None
        if patient_id and patient_id != "null" and patient_id != "undefined":
            try:
                p_uuid = uuid.UUID(patient_id)
                db_patient = db.query(Patient).filter(Patient.id == p_uuid).first()
            except ValueError:
                pass

        # If patient context exists, run through LangGraph agent to persist state
        if db_patient:
            state_input = {
                "patient_id": db_patient.id,
                "telegram_id": db_patient.telegram_id,
                "input_type": "voice",
                "raw_input_bytes": audio_bytes,
                "raw_input_text": None,
                "preferred_language": language.lower(),
                "extracted_data": {},
                "symptom_answers": {},
                "risk_level": "low",
                "risk_message": None,
                "chat_history": [],
                "response_english": "",
                "response_translated": "",
                "response_audio_bytes": None
            }
            output = compiled_aarogya_agent.invoke(state_input)
            
            transcript_en = output.get("raw_input_text") or ""
            response_text = output.get("response_translated") or ""
            response_audio = output.get("response_audio_bytes") or b""
        else:
            # General conversation without patient context
            # Determine transcript
            transcript_en = voice_service.transcribe_voice(audio_bytes, mime_type=mime_type)
            if not transcript_en:
                raise HTTPException(status_code=400, detail="Could not transcribe audio. Please speak clearly.")
            
            prompt = f"""
            You are AAROGYA, a helpful, knowledgeable, and empathetic AI rural healthcare companion.
            The user asks: "{transcript_en}"
            Provide a clear, simple, and reassuring medical response. Keep it brief and friendly.
            """
            resp_eng = gemini_service.generate_content(prompt)
            response_text = translation_service.translate_from_english(resp_eng, language.lower())
            response_audio = voice_service.synthesize_speech(response_text, language.lower())

        # Encode synthesized response to Base64
        audio_base64 = base64.b64encode(response_audio).decode("utf-8") if response_audio else ""

        return {
            "transcript": transcript_en,
            "response_text": response_text,
            "audio_base64": audio_base64
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice assistant processing failed: {str(e)}")
        return {
            "transcript": "",
            "response_text": (
                "Voice assistant is temporarily unavailable. "
                "Please try again or contact your healthcare worker."
            ),
            "audio_base64": "",
        }
