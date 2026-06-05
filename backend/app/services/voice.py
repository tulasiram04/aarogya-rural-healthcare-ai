import logging
import tempfile
import os
from gtts import gTTS
from app.services.gemini import gemini_service

logger = logging.getLogger("aarogya.voice")

class VoiceService:
    def transcribe_voice(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        """
        Transcribe voice note bytes (e.g. OGG/WAV) to English text using Gemini's multimodal audio input.
        """
        prompt = (
            "You are a clinical speech recognition model. Transcribe this audio recording precisely. "
            "If the speaker is talking in an Indian language (like Hindi, Tamil, Telugu, Kannada, Malayalam), "
            "translate their words directly to English text. Return only the transcription/translation."
        )
        try:
            # Send audio bytes directly into Gemini's multimodal engine
            response_text = gemini_service.generate_content(
                prompt=prompt,
                image_bytes=audio_bytes,
                image_mime=mime_type
            )
            return response_text.strip()
        except Exception as e:
            logger.error(f"Voice transcription failed: {str(e)}")
            return ""

    def synthesize_speech(self, text: str, lang: str) -> bytes:
        """
        Synthesize text into speech (TTS) bytes using gTTS (Google Text-to-Speech).
        Supports Indic regional language voice generation.
        """
        # Map languages to standard ISO 639-1 codes for gTTS
        lang_map = {
            "hindi": "hi",
            "tamil": "ta",
            "telugu": "te",
            "kannada": "kn",
            "malayalam": "ml",
            "english": "en"
        }
        iso_code = lang_map.get(lang.lower(), "en")
        
        try:
            # Write to a temporary file, read back bytes, and clean up
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_filename = f.name
            
            tts = gTTS(text=text, lang=iso_code, slow=False)
            tts.save(temp_filename)
            
            with open(temp_filename, "rb") as f:
                audio_bytes = f.read()
                
            os.remove(temp_filename)
            return audio_bytes
        except Exception as e:
            logger.error(f"Speech synthesis failed for lang {lang}: {str(e)}")
            # Return empty bytes on exception
            return b""

voice_service = VoiceService()
