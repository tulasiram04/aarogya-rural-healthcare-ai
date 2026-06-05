import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger("aarogya.gemini")

FALLBACK_MESSAGES = {
    "prescription": (
        "Prescription saved successfully. AI extraction is temporarily unavailable — "
        "please review the uploaded image manually."
    ),
    "report": (
        "Lab report saved successfully. AI analysis is temporarily unavailable — "
        "please review the uploaded report manually."
    ),
    "symptom": (
        "Symptom check-in recorded. AI assessment is temporarily unavailable — "
        "a healthcare worker will review your symptoms."
    ),
    "general": (
        "AI assistant is temporarily unavailable. Your request has been saved and "
        "will be reviewed by a healthcare worker shortly."
    ),
}


class GeminiService:
    def __init__(self):
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "PLACEHOLDER_GEMINI_KEY":
            genai.configure(api_key=settings.GEMINI_API_KEY)
        else:
            logger.warning("Gemini API key not configured. AI operations will return graceful fallbacks.")

    def generate_content(
        self,
        prompt: str,
        image_bytes: Optional[bytes] = None,
        image_mime: str = "image/jpeg",
        response_schema: Optional[Any] = None,
    ) -> str:
        """Generate text response from prompt, optionally including image bytes."""
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "PLACEHOLDER_GEMINI_KEY":
            return self._graceful_fallback(prompt)

        try:
            model_name = "gemini-2.5-flash"
            model = genai.GenerativeModel(model_name)

            contents = [prompt]
            if image_bytes:
                contents.append({"mime_type": image_mime, "data": image_bytes})

            generation_config = {}
            if response_schema:
                generation_config = {
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                }

            response = model.generate_content(contents, generation_config=generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API generation failed: {str(e)}")
            return self._graceful_fallback(prompt)

    def _graceful_fallback(self, prompt: str) -> str:
        """Return user-friendly fallback — never fake clinical data."""
        prompt_lower = prompt.lower()
        if "prescription" in prompt_lower or "medicine" in prompt_lower:
            return FALLBACK_MESSAGES["prescription"]
        if "report" in prompt_lower or "blood" in prompt_lower or "lab" in prompt_lower:
            return FALLBACK_MESSAGES["report"]
        if "symptom" in prompt_lower or "check-in" in prompt_lower:
            return FALLBACK_MESSAGES["symptom"]
        return FALLBACK_MESSAGES["general"]


gemini_service = GeminiService()
