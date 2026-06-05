import logging
import os
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# Adjust path to import backend packages
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

import app.models

from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.medical import ComplianceLog, Reminder
from app.services.translation import translation_service
from app.services.voice import voice_service
from app.agents.graph import compiled_aarogya_agent
from app.services.doctor_assignment import assign_doctor_to_patient
from app.services.activity import create_activity_log

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("aarogya.bot")

# Conversation States
ONBOARD_NAME, ONBOARD_AGE, ONBOARD_LANG = range(3)
SELECT_MEDIA_TYPE = 4

# Fetch token
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "PLACEHOLDER_TOKEN")

# Helper to check if patient is registered
def get_db_patient(telegram_id: int) -> Patient | None:
    db = SessionLocal()
    try:
        return db.query(Patient).filter(Patient.telegram_id == telegram_id).first()
    finally:
        db.close()

# --- Start Handler & Onboarding ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for patient registration or greets existing patient."""
    logger.info("START COMMAND HIT")
    logger.info(f"START received from user {update.effective_user.id}")
    try:
        user = update.effective_user
        patient = get_db_patient(user.id)
        
        if patient:
            lang = patient.preferred_language
            welcome_back = translation_service.get_static_text("welcome_back", lang, name=patient.full_name)
            
            # Display options
            keyboard = [
                [InlineKeyboardButton("📝 Daily Health Check-in", callback_data="checkin")],
                [InlineKeyboardButton("📄 Upload Prescription", callback_data="upload_rx")],
                [InlineKeyboardButton("🩸 Upload Lab Report", callback_data="upload_rep")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(welcome_back, reply_markup=reply_markup)
            return ConversationHandler.END

        # Start onboarding
        await update.message.reply_text(
            "Welcome to AAROGYA Rural Health Platform!\n"
            "I am your digital village doctor agent. Let's register you.\n\n"
            "What is your full name?"
        )
        return ONBOARD_NAME
    except Exception as e:
        logger.exception(f"START handler failed: {e}")
        await update.message.reply_text("Internal error occurred")


async def onboard_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores name and requests age."""
    context.user_data["full_name"] = update.message.text
    await update.message.reply_text("Got it! How old are you?")
    return ONBOARD_AGE


async def onboard_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores age and requests language selection."""
    age_text = update.message.text
    try:
        age = int(age_text)
    except ValueError:
        age = None
    context.user_data["age"] = age
    
    # Language choices keyboard
    keyboard = [
        [
            InlineKeyboardButton("Hindi (हिंदी)", callback_data="hindi"),
            InlineKeyboardButton("Tamil (தமிழ்)", callback_data="tamil"),
        ],
        [
            InlineKeyboardButton("Telugu (తెలుగు)", callback_data="telugu"),
            InlineKeyboardButton("Kannada (ಕನ್ನಡ)", callback_data="kannada"),
        ],
        [
            InlineKeyboardButton("Malayalam (മലയാളം)", callback_data="malayalam"),
            InlineKeyboardButton("English", callback_data="english"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Please select your preferred language for consultations and medicine reminders:",
        reply_markup=reply_markup
    )
    return ONBOARD_LANG


async def onboard_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Completes registration and persists details in PostgreSQL."""
    query = update.callback_query
    await query.answer()
    
    lang = query.data
    full_name = context.user_data["full_name"]
    age = context.user_data.get("age")
    telegram_id = query.from_user.id
    
    # Save patient to DB — Telegram bot is the ONLY registration path
    db = SessionLocal()
    try:
        existing = db.query(Patient).filter(Patient.telegram_id == telegram_id).first()
        if existing:
            lang = existing.preferred_language
            welcome_back = translation_service.get_static_text("welcome_back", lang, name=existing.full_name)
            await query.edit_message_text(welcome_back)
            return ConversationHandler.END

        new_patient = Patient(
            telegram_id=telegram_id,
            full_name=full_name,
            age=age,
            preferred_language=lang,
            medical_history={},
            is_demo=False,
        )
        
        # Auto doctor assignment
        assign_doctor_to_patient(db, new_patient)
        
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        
        logger.info("PATIENT REGISTERED")
        logger.info(f"PATIENT REGISTERED: ID={new_patient.id}, Name={new_patient.full_name}")
        create_activity_log(db, new_patient.id, "PATIENT_REGISTERED", f"👤 {new_patient.full_name} registered as a new patient", is_demo=False)
    except Exception as e:
        logger.error(f"Failed to save onboarding data: {str(e)}")
        db.rollback()
        await query.edit_message_text("Registration failed. Please send /start to try again.")
        return ConversationHandler.END
    finally:
        db.close()
        
    welcome_msg = translation_service.get_static_text("welcome", lang)
    await query.edit_message_text(f"Registration successful!\n\n{welcome_msg}")
    return ConversationHandler.END

# --- Message and Voice Chat Handler ---

async def handle_text_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text query from the patient and routes it through LangGraph Agent."""
    user = update.effective_user
    patient = get_db_patient(user.id)
    if not patient:
        await update.message.reply_text("Please register first by sending /start")
        return

    text = update.message.text
    await update.message.reply_chat_action("typing")

    input_type = "text"
    if context.user_data.get("awaiting_checkin"):
        input_type = "checkin"
        context.user_data.pop("awaiting_checkin", None)

    state_input = {
        "patient_id": patient.id,
        "telegram_id": patient.telegram_id,
        "input_type": input_type,
        "raw_input_bytes": None,
        "raw_input_text": text,
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

    output = compiled_aarogya_agent.invoke(state_input)
    response = output.get("response_translated")
    await update.message.reply_text(response)


async def handle_voice_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Downloads voice memo, transcribes it, runs agent logic, and responds with audio TTS."""
    user = update.effective_user
    patient = get_db_patient(user.id)
    if not patient:
        await update.message.reply_text("Please register first by sending /start")
        return

    voice = update.message.voice
    audio = update.message.audio
    
    file_id = None
    mime_type = "audio/ogg"
    
    if voice:
        file_id = voice.file_id
        mime_type = voice.mime_type or "audio/ogg"
    elif audio:
        file_id = audio.file_id
        mime_type = audio.mime_type or "audio/mpeg"
        
    if not file_id:
        await update.message.reply_text("Could not extract audio or voice note.")
        return

    # Download file bytes
    voice_file = await context.bot.get_file(file_id)
    voice_bytes = await voice_file.download_as_bytearray()
    
    await update.message.reply_chat_action("record_voice")

    state_input = {
        "patient_id": patient.id,
        "telegram_id": patient.telegram_id,
        "input_type": "voice",
        "raw_input_bytes": bytes(voice_bytes),
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

    output = compiled_aarogya_agent.invoke(state_input)
    response_text = output.get("response_translated")
    audio_bytes = output.get("response_audio_bytes")

    await update.message.reply_text(response_text)
    
    if audio_bytes:
        # Send voice note reply to patient
        await update.message.reply_voice(voice=audio_bytes)

# --- Media OCR Upload Handlers ---

async def handle_photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Intercepts photo and asks user to identify file type (Prescription vs Report)."""
    user = update.effective_user
    patient = get_db_patient(user.id)
    if not patient:
        await update.message.reply_text("Please register first by sending /start")
        return

    photo = update.message.photo[-1] # Highest resolution photo
    photo_file = await context.bot.get_file(photo.file_id)
    photo_bytes = await photo_file.download_as_bytearray()
    media_bytes = bytes(photo_bytes)
    
    awaiting = context.user_data.get("awaiting_upload")
    if awaiting in ["prescription", "report"]:
        context.user_data.pop("awaiting_upload", None)
        await update.message.reply_text("🔄 Processing document... please wait. This can take a few seconds.")
        
        state_input = {
            "patient_id": patient.id,
            "telegram_id": patient.telegram_id,
            "input_type": awaiting,
            "raw_input_bytes": media_bytes,
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

        output = compiled_aarogya_agent.invoke(state_input)
        response_translated = output.get("response_translated")
        await update.message.reply_text(response_translated)
        return

    # Store bytes in context memory temporarily
    context.user_data["uploaded_media"] = media_bytes
    
    keyboard = [
        [
            InlineKeyboardButton("📄 Prescription (नुस्खा)", callback_data="media_rx"),
            InlineKeyboardButton("🩸 Lab Report (रिपोर्ट)", callback_data="media_report")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "I have received the image. Please select what this document is:",
        reply_markup=reply_markup
    )


async def handle_media_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes prescription/report image through LangGraph OCR pipeline."""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    patient = get_db_patient(user.id)
    media_bytes = context.user_data.get("uploaded_media")
    
    if not media_bytes or not patient:
        await query.edit_message_text("Session expired. Please re-upload the image.")
        return
        
    selection = query.data
    await query.edit_message_text("🔄 Processing document... please wait. This can take a few seconds.")
    
    input_type = "prescription" if selection == "media_rx" else "report"
    
    state_input = {
        "patient_id": patient.id,
        "telegram_id": patient.telegram_id,
        "input_type": input_type,
        "raw_input_bytes": media_bytes,
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

    output = compiled_aarogya_agent.invoke(state_input)
    response_translated = output.get("response_translated")
    
    await query.edit_message_text(response_translated)
    
    # Clear memory cache
    context.user_data.pop("uploaded_media", None)

# --- Compliance Logs Handler ---

async def handle_compliance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes inline response for medication taken vs missed."""
    query = update.callback_query
    await query.answer()
    
    data = query.data # "compliance_taken_<log_id>" or "compliance_missed_<log_id>"
    action, log_id = data.split("_", 1)
    
    db = SessionLocal()
    try:
        log = db.query(ComplianceLog).filter(ComplianceLog.id == log_id).first()
        if log:
            log.status = "taken" if action == "taken" else "missed"
            log.taken_time = datetime.now(timezone.utc)
            db.commit()
            
            patient = log.reminder.patient
            # Log Activity
            if action == "taken":
                create_activity_log(db, patient.id, "REMINDER_COMPLETED", f"✅ {patient.full_name} took dose of {log.reminder.medicine_name}")
            else:
                create_activity_log(db, patient.id, "REMINDER_MISSED", f"❌ {patient.full_name} missed dose of {log.reminder.medicine_name}")
                
            thanks_msg = translation_service.get_static_text("compliance_thanks", patient.preferred_language)
            await query.edit_message_text(f"Thank you. Log updated: {action.upper()}.\n\n{thanks_msg}")
        else:
            await query.edit_message_text("Reminder window expired.")
    except Exception as e:
        logger.error(f"Compliance callback fail: {str(e)}")
        db.rollback()
    finally:
        db.close()

# --- Debug & Error Handlers ---

async def error_handler(update, context):
    logger.exception("Unhandled exception", exc_info=context.error)

async def debug_update(update, context):
    logger.info(f"UPDATE RECEIVED: {update}")

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"MENU CALLBACK HIT: {data}")
    
    if data == "checkin":
        context.user_data["awaiting_checkin"] = True
        await query.message.reply_text(
            "Please describe your symptoms today in detail (e.g. fever, cough, shortness of breath):"
        )
    elif data == "upload_rx":
        context.user_data["awaiting_upload"] = "prescription"
        await query.message.reply_text("Please upload a prescription image.")
    elif data == "upload_rep":
        context.user_data["awaiting_upload"] = "report"
        await query.message.reply_text("Please upload a lab report image.")

# --- Main Application Loop ---

def main() -> None:
    """Build and launch the Bot application worker."""
    if not BOT_TOKEN or BOT_TOKEN == "PLACEHOLDER_TOKEN":
        logger.error("TELEGRAM_BOT_TOKEN missing. Set it in .env and restart the bot container.")
        return

    import httpx
    try:
        resp = httpx.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
        data = resp.json()
        if not data.get("ok"):
            logger.error(
                "TELEGRAM_BOT_TOKEN is invalid or revoked. "
                "Get a new token from @BotFather, update .env, then run: docker compose restart telegram_bot"
            )
            return
        bot_name = data.get("result", {}).get("username", "unknown")
        logger.info(f"Telegram bot authenticated: @{bot_name}")
    except Exception as e:
        logger.error(f"Could not verify Telegram token: {e}")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation setup for onboarding registration
    onboard_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ONBOARD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_name)],
            ONBOARD_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboard_age)],
            ONBOARD_LANG: [CallbackQueryHandler(onboard_lang)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Register handlers
    application.add_error_handler(error_handler)
    
    application.add_handler(
        MessageHandler(filters.ALL, debug_update),
        group=999
    )
    
    application.add_handler(
        CallbackQueryHandler(
            handle_menu_callback,
            pattern="^(checkin|upload_rx|upload_rep)$"
        )
    )
    
    application.add_handler(onboard_conv)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_chat))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_chat))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_upload))
    application.add_handler(CallbackQueryHandler(handle_media_selection, pattern="^media_"))
    application.add_handler(CallbackQueryHandler(handle_compliance_callback, pattern="^(taken|missed)_"))
    
    # Print all registered handlers at startup
    logger.info("Registered handlers list:")
    for group, handlers in application.handlers.items():
        logger.info(f"Group {group}: {[type(h).__name__ for h in handlers]}")
        
    # Run Bot
    logger.info("AAROGYA bot handler starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
