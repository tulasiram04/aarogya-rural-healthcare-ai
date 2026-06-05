import logging
from typing import Dict
from app.services.gemini import gemini_service

logger = logging.getLogger("aarogya.translation")

# Static dictionary for low-latency common bot phrases across supported languages
STATIC_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "hindi": {
        "welcome": "आरोग्य में आपका स्वागत है। मैं आपका डिजिटल ग्राम डॉक्टर हूँ। कृपया अपनी भाषा चुनें।",
        "welcome_back": "नमस्ते {name}, आशा है कि आप ठीक होंगे। क्या आपने आज की दवा ली?",
        "taken": "💊 ले लिया",
        "missed": "❌ छूट गया",
        "upload_rx": "कृपया अपने नुस्खे (Prescription) की तस्वीर अपलोड करें।",
        "upload_report": "कृपया अपनी लैब रिपोर्ट की तस्वीर अपलोड करें।",
        "compliance_thanks": "पुष्टि करने के लिए धन्यवाद। मैंने आपकी दवा अनुपालन दर्ज कर ली है।",
        "daily_checkin": "नमस्ते! आपका दैनिक स्वास्थ्य अपडेट लेने का समय हो गया है। क्या आपको आज कोई लक्षण (जैसे बुखार, खांसी या दर्द) महसूस हो रहा है?",
    },
    "tamil": {
        "welcome": "ஆரோக்கியாவிற்கு உங்களை வரவேற்கிறோம். நான் உங்கள் டிஜிட்டல் கிராம மருத்துவர். தயவுசெய்து உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்.",
        "welcome_back": "வணக்கம் {name}, நீங்கள் நலம் என நம்புகிறேன். இன்று உங்கள் மருந்துகளை உட்கொண்டீர்களா?",
        "taken": "💊 சாப்பிட்டேன்",
        "missed": "❌ தவறவிட்டேன்",
        "upload_rx": "தயவுசெய்து உங்கள் மருந்துச் சீட்டின் (Prescription) புகைப்படத்தைப் பதிவேற்றவும்.",
        "upload_report": "தயவுசெய்து உங்கள் இரத்த பரிசோதனை அறிக்கையைப் பதிவேற்றவும்.",
        "compliance_thanks": "உறுதிப்படுத்தியதற்கு நன்றி. உங்கள் மருந்து உட்கொள்ளல் பதிவு செய்யப்பட்டது.",
        "daily_checkin": "வணக்கம்! உங்கள் தினசரி உடல்நல விவரங்களை அறியும் நேரம் இது. இன்று உங்களுக்கு காய்ச்சல், இருமல் அல்லது வலி போன்ற ஏதேனும் அறிகுறிகள் உள்ளதா?",
    },
    "telugu": {
        "welcome": "ఆరోగ్యకు స్వాగతం. నేను మీ డిజిటల్ గ్రామ వైద్యుడిని. దయచేసి మీ భాషను ఎంచుకోండి.",
        "welcome_back": "నమస్తే {name}, మీరు బాగున్నారని ఆశిస్తున్నాను. ఈరోజు మీ మందులు వేసుకున్నారా?",
        "taken": "💊 వేసుకున్నాను",
        "missed": "❌ వేసుకోలేదు",
        "upload_rx": "దయచేసి మీ ప్రిస్క్రిప్షన్ ఫోటోను అప్‌లోడ్ చేయండి.",
        "upload_report": "దయచేసి మీ ల్యాబ్ రిపోర్ట్ అప్‌లోడ్ చేయండి.",
        "compliance_thanks": "ధృవీకరించినందుకు ధన్యవాదాలు. మీ మందుల వివరాలు నమోదు చేయబడ్డాయి.",
        "daily_checkin": "నమస్తే! మీ రోజువారీ ఆరోగ్య సమాచారాన్ని నమోదు చేసే సమయం అయింది. ఈరోజు మీకు జ్వరం, దగ్గు లేదా నొప్పులు వంటి ఏవైనా లక్షణాలు ఉన్నాయా?",
    },
    "kannada": {
        "welcome": "ಆರೋಗ್ಯಕ್ಕೆ ಸುಸ್ವಾಗತ. ನಾನು ನಿಮ್ಮ ಡಿಜಿಟಲ್ ಗ್ರಾಮ ವೈದ್ಯ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ.",
        "welcome_back": "ನಮಸ್ತೆ {name}, ನೀವು ಆರಾಮವಾಗಿದ್ದೀರಿ ಎಂದು ಭಾವಿಸುತ್ತೇನೆ. ಇಂದಿನ ಔಷಧಿ ತೆಗೆದುಕೊಂಡಿರಾ?",
        "taken": "💊 ತೆಗೆದುಕೊಂಡಿದ್ದೇನೆ",
        "missed": "❌ ತಪ್ಪಿಹೋಗಿದೆ",
        "upload_rx": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "upload_report": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಲ್ಯಾಬ್ ವರದಿಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "compliance_thanks": "ದೃಢೀಕರಿಸಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು. ನಿಮ್ಮ ಔಷಧಿ ವಿವರ ದಾಖಲಾಗಿದೆ.",
        "daily_checkin": "ನಮಸ್ತೆ! ನಿಮ್ಮ ದೈನಂದಿನ ಆರೋಗ್ಯದ ಸ್ಥಿತಿಯನ್ನು ತಿಳಿಸುವ ಸಮಯ. ಇಂದು ನಿಮಗೆ ಜ್ವರ, ಕೆಮ್ಮು ಅಥವಾ ಮೈ ಕೈ ನೋವು ಯಾವುದಾದರೂ ಇದೆಯೇ?",
    },
    "malayalam": {
        "welcome": "ആരോഗ്യയിലേക്ക് സ്വാഗതം. ഞാൻ നിങ്ങളുടെ ഡിജിറ്റൽ ഗ്രാമ ഡോക്ടറാണ്. ദയവായി നിങ്ങളുടെ ഭാഷ തിരഞ്ഞെടുക്കുക.",
        "welcome_back": "നമസ്തേ {name}, സുഖമാണെന്ന് കരുതുന്നു. ഇന്ന് മരുന്ന് കഴിച്ചോ?",
        "taken": "💊 കഴിച്ചു",
        "missed": "❌ കഴിച്ചില്ല",
        "upload_rx": "ദയവായി നിങ്ങളുടെ പ്രിസ്ക്രിപ്ഷൻ ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക.",
        "upload_report": "ദയവായി നിങ്ങളുടെ ലാബ് റിപ്പോർട്ട് അപ്‌ലോഡ് ചെയ്യുക.",
        "compliance_thanks": "സ്ഥിരീകരിച്ചതിന് നന്ദി. നിങ്ങളുടെ മരുന്ന് വിവരങ്ങൾ രേഖപ്പെടുത്തിയിട്ടുണ്ട്.",
        "daily_checkin": "നമസ്തേ! നിങ്ങളുടെ ദിവസേനയുള്ള ആരോഗ്യവിവരങ്ങൾ രേഖപ്പെടുത്തേണ്ട സമയമായി. ഇന്ന് പനി, ചുമ അല്ലെങ്കിൽ മറ്റ്‌ അസ്വസ്ഥതകൾ ഉണ്ടോ?",
    },
    "english": {
        "welcome": "Welcome to AAROGYA. I am your digital village doctor. Please select your preferred language.",
        "welcome_back": "Hello {name}, hope you are doing well. Have you taken your scheduled medicines today?",
        "taken": "💊 Taken",
        "missed": "❌ Missed",
        "upload_rx": "Please upload a photo of your prescription.",
        "upload_report": "Please upload a photo of your lab reports.",
        "compliance_thanks": "Thank you for confirming. I have logged your compliance.",
        "daily_checkin": "Hello! It is time for your daily health check-in. Are you experiencing any symptoms (like fever, cough, or pain) today?",
    }
}

class TranslationService:
    def get_static_text(self, key: str, lang: str, **kwargs) -> str:
        """Fetch pre-translated phrases for instant performance and zero LLM billing."""
        lang_lower = lang.lower()
        if lang_lower not in STATIC_TRANSLATIONS:
            lang_lower = "english"
        
        phrases = STATIC_TRANSLATIONS.get(lang_lower, STATIC_TRANSLATIONS["english"])
        raw_text = phrases.get(key, STATIC_TRANSLATIONS["english"].get(key, ""))
        return raw_text.format(**kwargs) if kwargs else raw_text

    def translate_to_english(self, text: str, source_lang: str) -> str:
        """
        Translate input text from local language to English (backend processing).
        """
        if source_lang.lower() == "english" or not text.strip():
            return text

        prompt = f"Translate the following patient communication from {source_lang} to English. Keep medical terms accurate:\n\n{text}"
        try:
            return gemini_service.generate_content(prompt).strip()
        except Exception as e:
            logger.error(f"Translation to English failed: {str(e)}")
            return text

    def translate_from_english(self, text: str, target_lang: str) -> str:
        """
        Translate clinical output from English to patient's target local language.
        """
        if target_lang.lower() == "english" or not text.strip():
            return text

        prompt = (
            f"Translate the following medical guidance from English to {target_lang}. "
            f"Use simple, easy-to-understand words that a rural villager can understand. "
            f"Keep medicine names and dosages in English characters if they are transliterated, e.g., 'Metformin 500mg' remains 'Metformin 500mg' in the script:\n\n{text}"
        )
        try:
            return gemini_service.generate_content(prompt).strip()
        except Exception as e:
            logger.error(f"Translation from English failed: {str(e)}")
            return text

translation_service = TranslationService()
