import logging
import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
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
from app.mcp.server import call_mcp_tool

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("aarogya.bot")

# Conversation States
ONBOARD_NAME, ONBOARD_AGE, ONBOARD_GENDER = range(3)
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

def calculate_completion(patient: Patient) -> int:
    completion = 60
    if patient.village:
        completion += 20
    if patient.phone:
        completion += 10
    if patient.blood_group:
        completion += 10
    return completion

async def check_and_prompt_progressive(telegram_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.telegram_id == telegram_id).first()
        if not patient:
            return
        
        # Sync completion percentage in DB
        completion = calculate_completion(patient)
        if patient.profile_completion != completion:
            patient.profile_completion = completion
            db.commit()
            db.refresh(patient)

        # Check if village is missing
        if not patient.village:
            postponed = patient.medical_history.get("village_prompt_postponed", False)
            postponed_time_str = patient.medical_history.get("village_prompt_time")
            should_prompt = True
            
            if postponed and postponed_time_str:
                try:
                    postponed_time = datetime.fromisoformat(postponed_time_str)
                    if datetime.now(timezone.utc) - postponed_time < timedelta(hours=24):
                        should_prompt = False
                except Exception as time_err:
                    logger.error(f"Error checking village postponement: {time_err}")
            
            if should_prompt:
                keyboard = [
                    [
                        InlineKeyboardButton("🏡 Enter Village", callback_data="prompt_village_enter"),
                        InlineKeyboardButton("⏭ Skip For Now", callback_data="prompt_village_skip"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                msg = (
                    "🏡 Help us personalize your healthcare experience.\n\n"
                    "Which village or town are you from?"
                )
                if update.callback_query:
                    await update.callback_query.message.reply_text(msg, reply_markup=reply_markup)
                else:
                    await update.message.reply_text(msg, reply_markup=reply_markup)
                return

        # If village is collected, check optional details (Phone & Blood Group)
        if patient.village:
            if not patient.phone or not patient.blood_group:
                postponed = patient.medical_history.get("details_prompt_postponed", False)
                postponed_time_str = patient.medical_history.get("details_prompt_time")
                should_prompt = True
                
                if postponed and postponed_time_str:
                    try:
                        postponed_time = datetime.fromisoformat(postponed_time_str)
                        if datetime.now(timezone.utc) - postponed_time < timedelta(hours=24):
                            should_prompt = False
                    except Exception as time_err:
                        logger.error(f"Error checking details postponement: {time_err}")
                
                if should_prompt:
                    keyboard = [
                        [
                            InlineKeyboardButton("📱 Add Details", callback_data="prompt_details_add"),
                            InlineKeyboardButton("⏭ Maybe Later", callback_data="prompt_details_skip"),
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    msg = (
                        "💚 Complete Your Health Profile\n\n"
                        "Optional information:\n\n"
                        "📱 Phone Number\n"
                        "🩸 Blood Group\n\n"
                        "These help improve emergency support."
                    )
                    if update.callback_query:
                        await update.callback_query.message.reply_text(msg, reply_markup=reply_markup)
                    else:
                        await update.message.reply_text(msg, reply_markup=reply_markup)
    except Exception as e:
        logger.exception(f"Error in check_and_prompt_progressive: {e}")
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
            welcome_back = (
                f"🌿 Welcome back to AAROGYA, {patient.full_name}!\n\n"
                "📸 Send a prescription image or ask me any healthcare question to get started."
            )
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
            "🌿 Welcome to AAROGYA\n\n"
            "AI-Powered Rural Healthcare Companion\n\n"
            "Let's create your health profile.\n\n"
            "👤 What is your name?"
        )
        return ONBOARD_NAME
    except Exception as e:
        logger.exception(f"START handler failed: {e}")
        await update.message.reply_text("Internal error occurred")


async def onboard_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores name and requests age."""
    context.user_data["full_name"] = update.message.text
    await update.message.reply_text("📅 What is your age?")
    return ONBOARD_AGE


async def onboard_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores age and requests gender selection."""
    age_text = update.message.text
    try:
        age = int(age_text)
    except ValueError:
        age = None
    context.user_data["age"] = age
    
    keyboard = [
        [
            InlineKeyboardButton("👨 Male", callback_data="gender_Male"),
            InlineKeyboardButton("👩 Female", callback_data="gender_Female"),
            InlineKeyboardButton("⚧ Other", callback_data="gender_Other"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚧ Select your gender",
        reply_markup=reply_markup
    )
    return ONBOARD_GENDER


async def onboard_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Completes registration and persists details in PostgreSQL."""
    query = update.callback_query
    await query.answer()
    
    gender = query.data.replace("gender_", "")
    full_name = context.user_data["full_name"]
    age = context.user_data.get("age")
    telegram_id = query.from_user.id
    
    db = SessionLocal()
    try:
        existing = db.query(Patient).filter(Patient.telegram_id == telegram_id).first()
        if existing:
            welcome_back = (
                f"🌿 Welcome back to AAROGYA, {existing.full_name}!\n\n"
                "📸 Send a prescription image or ask me any healthcare question to get started."
            )
            await query.edit_message_text(welcome_back)
            return ConversationHandler.END

        new_patient = Patient(
            telegram_id=telegram_id,
            full_name=full_name,
            age=age,
            gender=gender,
            preferred_language="english",
            village=None,
            phone=None,
            blood_group=None,
            profile_completion=60,
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
        
    completion_msg = (
        "🎉 Registration Complete\n\n"
        f"👤 Name: {full_name}\n"
        f"📅 Age: {age if age is not None else 'N/A'}\n"
        f"⚧ Gender: {gender}\n\n"
        "📊 Profile Completion: 60%\n\n"
        "✅ Health Profile Created\n"
        "✅ AI Assistant Activated\n"
        "✅ Prescription Analysis Ready\n"
        "✅ Medicine Reminders Ready\n\n"
        "📸 Send a prescription image to get started."
    )
    await query.edit_message_text(completion_msg)
    return ConversationHandler.END

# --- Message and Voice Chat Handler ---

async def handle_text_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles text query from the patient and routes it through LangGraph Agent."""
    user = update.effective_user
    patient = get_db_patient(user.id)
    if not patient:
        await update.message.reply_text("Please register first by sending /start")
        return

    text = update.message.text.strip()

    # Intercept progressive onboarding responses
    if context.user_data.get("awaiting_village"):
        context.user_data.pop("awaiting_village", None)
        db = SessionLocal()
        try:
            db_patient = db.query(Patient).filter(Patient.id == patient.id).first()
            if db_patient:
                db_patient.village = text
                db_patient.profile_completion = calculate_completion(db_patient)
                db.commit()
                db.refresh(db_patient)
                await update.message.reply_text(
                    f"✅ Village updated to: {text}\n"
                    f"📊 Profile Completion: {db_patient.profile_completion}%\n\n"
                    f"Let's complete the remaining optional details."
                )
                await check_and_prompt_progressive(db_patient.telegram_id, update, context)
        except Exception as e:
            logger.error(f"Error saving village text: {e}")
            db.rollback()
        finally:
            db.close()
        return

    if context.user_data.get("awaiting_phone"):
        context.user_data.pop("awaiting_phone", None)
        db = SessionLocal()
        try:
            db_patient = db.query(Patient).filter(Patient.id == patient.id).first()
            if db_patient:
                db_patient.phone = text
                db_patient.profile_completion = calculate_completion(db_patient)
                db.commit()
                db.refresh(db_patient)
                await update.message.reply_text(
                    f"✅ Phone number updated to: {text}\n"
                    f"📊 Profile Completion: {db_patient.profile_completion}%"
                )
                context.user_data["awaiting_blood_group"] = True
                keyboard = [
                    [
                        InlineKeyboardButton("A+", callback_data="blood_A+"),
                        InlineKeyboardButton("A-", callback_data="blood_A-"),
                        InlineKeyboardButton("B+", callback_data="blood_B+"),
                        InlineKeyboardButton("B-", callback_data="blood_B-"),
                    ],
                    [
                        InlineKeyboardButton("AB+", callback_data="blood_AB+"),
                        InlineKeyboardButton("AB-", callback_data="blood_AB-"),
                        InlineKeyboardButton("O+", callback_data="blood_O+"),
                        InlineKeyboardButton("O-", callback_data="blood_O-"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("🩸 Please select your blood group:", reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error saving phone: {e}")
            db.rollback()
        finally:
            db.close()
        return

    if context.user_data.get("awaiting_blood_group"):
        context.user_data.pop("awaiting_blood_group", None)
        db = SessionLocal()
        try:
            db_patient = db.query(Patient).filter(Patient.id == patient.id).first()
            if db_patient:
                db_patient.blood_group = text.upper()
                db_patient.profile_completion = calculate_completion(db_patient)
                db.commit()
                db.refresh(db_patient)
                await update.message.reply_text(
                    f"✅ Blood Group updated to: {text.upper()}\n\n"
                    f"🎉 Health Profile Completed!\n"
                    f"📊 Profile Completion: {db_patient.profile_completion}%"
                )
        except Exception as e:
            logger.error(f"Error saving blood group text: {e}")
            db.rollback()
        finally:
            db.close()
        return

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
        "response_audio_bytes": None,
        "mcp_context": None
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
        "response_audio_bytes": None,
        "mcp_context": None
    }

    output = compiled_aarogya_agent.invoke(state_input)
    response_text = output.get("response_translated")
    audio_bytes = output.get("response_audio_bytes")

    await update.message.reply_text(response_text)
    
    if audio_bytes:
        # Send voice note reply to patient
        await update.message.reply_voice(voice=audio_bytes)

def get_progress_message(percentage: int) -> str:
    if percentage == 10:
        return (
            "📸 Prescription Received\n\n"
            "⏳ Estimated Processing Time: 8–12 seconds\n\n"
            "🧠 AI Processing Started...\n\n"
            "▰▱▱▱▱▱▱▱▱▱ 10%\n\n"
            "Saving image..."
        )
    elif percentage == 30:
        return (
            "🔍 OCR Extraction\n\n"
            "▰▰▰▱▱▱▱▱▱▱ 30%\n\n"
            "Reading prescription text..."
        )
    elif percentage == 60:
        return (
            "💊 Medicine Detection\n\n"
            "▰▰▰▰▰▰▱▱▱▱ 60%\n\n"
            "Identifying medicines..."
        )
    elif percentage == 85:
        return (
            "📅 Reminder Generation\n\n"
            "▰▰▰▰▰▰▰▰▱▱ 85%\n\n"
            "Scheduling reminders..."
        )
    elif percentage == 100:
        return (
            "✅ Analysis Complete\n\n"
            "▰▰▰▰▰▰▰▰▰▰ 100%\n\n"
            "Preparing final report..."
        )
    return ""

async def process_prescription_flow(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    media_bytes: bytes,
    progress_msg,
    query=None
) -> None:
    user = update.effective_user if update.effective_user else (query.from_user if query else None)
    if not user:
        return
        
    patient = get_db_patient(user.id)
    if not patient:
        return

    loop = asyncio.get_running_loop()
    last_percentage = 0

    async def update_progress_ui(percentage: int):
        nonlocal last_percentage
        if percentage <= last_percentage:
            return
        last_percentage = percentage
        try:
            msg_text = get_progress_message(percentage)
            if query:
                await query.edit_message_text(msg_text)
            else:
                await progress_msg.edit_text(msg_text)
        except Exception as edit_err:
            logger.error(f"Error updating progress message to {percentage}%: {edit_err}")

    def progress_callback(percentage: int):
        asyncio.run_coroutine_threadsafe(update_progress_ui(percentage), loop)

    # Initial state
    await update_progress_ui(10)

    # Prepare inputs for the LangGraph agent
    state_input = {
        "patient_id": patient.id,
        "telegram_id": patient.telegram_id,
        "input_type": "prescription",
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
        "response_audio_bytes": None,
        "mcp_context": None,
        "progress_callback": progress_callback
    }

    try:
        output = await asyncio.to_thread(compiled_aarogya_agent.invoke, state_input)
    except Exception as e:
        logger.exception(f"Error running agent invoke: {e}")
        error_text = (
            "❌ Unable to read prescription.\n\n"
            "Please upload a clearer image.\n\n"
            "Supported:\n"
            "✓ JPG\n"
            "✓ PNG\n"
            "✓ High-quality camera photos"
        )
        if query:
            await query.edit_message_text(error_text)
        else:
            await progress_msg.edit_text(error_text)
        return

    # Check if OCR failed or returned empty medicines
    meds = output.get("extracted_data", {}).get("medicines", [])
    diagnosis = output.get("extracted_data", {}).get("diagnosis", "")
    
    if not meds or diagnosis == "Analysis Unavailable":
        error_text = (
            "❌ Unable to read prescription.\n\n"
            "Please upload a clearer image.\n\n"
            "Supported:\n"
            "✓ JPG\n"
            "✓ PNG\n"
            "✓ High-quality camera photos"
        )
        if query:
            await query.edit_message_text(error_text)
        else:
            await progress_msg.edit_text(error_text)
        return

    # 100% complete
    await update_progress_ui(100)
    await asyncio.sleep(1.0)

    # Format final prescription report
    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    meds_lines = []
    for idx, med in enumerate(meds):
        emoji = number_emojis[idx] if idx < len(number_emojis) else f"{idx+1}️⃣"
        meds_lines.append(
            f"{emoji} {med.get('name', 'Unknown Medicine')}\n\n"
            f"• Dose: {med.get('dosage', '1 Tablet')}\n\n"
            f"• Frequency: {med.get('frequency', 'Once Daily')}\n\n"
            f"• Duration: {med.get('duration', '7 Days')}"
        )
    meds_block = "\n\n".join(meds_lines)

    insights = []
    has_diabetes = False
    has_bp = False

    diabetes_keywords = [
        "metformin", "glucophage", "glipizide", "glyburide", "gliclazide", "glimepiride", "amaryl", 
        "insulin", "lantus", "humalog", "novolog", "januvia", "sitagliptin", "jardiance", "empagliflozin", 
        "farxiga", "dapagliflozin", "victoza", "liraglutide", "ozempic", "semaglutide", "pioglitazone", 
        "actos", "acarbose"
    ]

    bp_keywords = [
        "amlodipine", "norvasc", "lisinopril", "zestril", "losartan", "cozaar", "telmisartan", "micardis", 
        "ramipril", "altace", "enalapril", "vasotec", "atenolol", "tenormin", "metoprolol", "lopressor", 
        "toprol", "propranolol", "inderal", "valsartan", "diovan", "hydrochlorothiazide", "hctz", 
        "diltiazem", "cardizem", "verapamil", "calan", "clonidine", "catapres", "spironolactone", 
        "aldactone", "nebivolol", "carvedilol", "coreg"
    ]

    for med in meds:
        med_name = med.get("name", "").lower()
        if any(k in med_name for k in diabetes_keywords):
            has_diabetes = True
        if any(k in med_name for k in bp_keywords):
            has_bp = True

    if has_diabetes:
        insights.append("⚠️ Diabetes medication detected")
    if has_bp:
        insights.append("⚠️ Blood pressure medication detected")
    insights.append("📅 Follow-up recommended")
    insights_block = "\n\n".join(insights)

    final_report = (
        "📋 PRESCRIPTION ANALYSIS COMPLETE\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"💊 Medicines Identified: {len(meds)}\n\n"
        f"📅 Reminders Scheduled: {len(meds)}\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"{meds_block}\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        "⏰ Reminder Status\n\n"
        "✅ All reminders scheduled\n\n"
        "✅ Adherence tracking enabled\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        "🤖 AAROGYA AI Insights\n\n"
        f"{insights_block}\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        "💚 Your medicines are now being monitored by AAROGYA."
    )

    if query:
        await query.edit_message_text(final_report)
    else:
        await progress_msg.edit_text(final_report)

    # Check/Prompt progressive onboarding details (Value-driven trigger)
    await check_and_prompt_progressive(patient.telegram_id, update, context)

async def prompt_village_enter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_village"] = True
    await query.edit_message_text("🏡 Please type the name of your village or town:")

async def prompt_village_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.telegram_id == telegram_id).first()
        if patient:
            med_hist = dict(patient.medical_history or {})
            med_hist["village_prompt_postponed"] = True
            med_hist["village_prompt_time"] = datetime.now(timezone.utc).isoformat()
            patient.medical_history = med_hist
            db.commit()
    except Exception as e:
        logger.error(f"Error skipping village: {e}")
        db.rollback()
    finally:
        db.close()
        
    await query.edit_message_text("No problem! We'll ask you again in 24 hours. You can always complete your profile via /profile.")

async def prompt_details_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data["awaiting_phone"] = True
    await query.edit_message_text("📱 Please enter your phone number:")

async def prompt_details_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.telegram_id == telegram_id).first()
        if patient:
            med_hist = dict(patient.medical_history or {})
            med_hist["details_prompt_postponed"] = True
            med_hist["details_prompt_time"] = datetime.now(timezone.utc).isoformat()
            patient.medical_history = med_hist
            db.commit()
    except Exception as e:
        logger.error(f"Error skipping details: {e}")
        db.rollback()
    finally:
        db.close()
        
    await query.edit_message_text("No problem! We'll ask you again in 24 hours. You can always complete your profile via /profile.")

async def blood_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    blood_group = query.data.replace("blood_", "")
    telegram_id = query.from_user.id
    
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.telegram_id == telegram_id).first()
        if patient:
            patient.blood_group = blood_group
            patient.profile_completion = calculate_completion(patient)
            db.commit()
            db.refresh(patient)
            await query.edit_message_text(
                f"✅ Blood Group updated to: {blood_group}\n\n"
                f"🎉 Health Profile Completed!\n"
                f"📊 Profile Completion: {patient.profile_completion}%"
            )
    except Exception as e:
        logger.error(f"Error saving blood group: {e}")
        db.rollback()
    finally:
        db.close()

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the patient's profile information and completion status."""
    user = update.effective_user
    patient = get_db_patient(user.id)
    if not patient:
        await update.message.reply_text("Please register first by sending /start")
        return
        
    completion = calculate_completion(patient)
    
    db = SessionLocal()
    try:
        db_patient = db.query(Patient).filter(Patient.id == patient.id).first()
        if db_patient and db_patient.profile_completion != completion:
            db_patient.profile_completion = completion
            db.commit()
    except Exception as e:
        logger.error(f"Error updating completion in /profile: {e}")
    finally:
        db.close()

    missing = []
    if not patient.village:
        missing.append("🏡 Village")
    if not patient.phone:
        missing.append("📱 Phone Number")
    if not patient.blood_group:
        missing.append("🩸 Blood Group")

    missing_str = ""
    if missing:
        missing_str = "\n⚠️ *Missing Fields:*\n" + "\n".join([f"  • {m}" for m in missing]) + "\n"

    msg = (
        "👤 *Patient Profile*\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"👤 Name: {patient.full_name}\n"
        f"📅 Age: {patient.age if patient.age is not None else 'N/A'}\n"
        f"⚧ Gender: {patient.gender or 'N/A'}\n"
        f"🏘️ Village: {patient.village or 'Not Set ❌'}\n"
        f"📱 Phone: {patient.phone or 'Not Set ❌'}\n"
        f"🩸 Blood Group: {patient.blood_group or 'Not Set ❌'}\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        f"📊 *Profile Completion: {completion}%*\n"
        f"{missing_str}"
    )
    
    keyboard = []
    if completion < 100:
        if not patient.village:
            keyboard.append([InlineKeyboardButton("🏡 Add Village", callback_data="prompt_village_enter")])
        if not patient.phone or not patient.blood_group:
            keyboard.append([InlineKeyboardButton("📱 Complete Optional Details", callback_data="prompt_details_add")])
            
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

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
        
        if awaiting == "prescription":
            progress_msg = await update.message.reply_text(get_progress_message(10))
            await process_prescription_flow(update, context, media_bytes, progress_msg)
            return
        else: # report
            progress_msg = await update.message.reply_text("🔄 Processing document... please wait. This can take a few seconds.")
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
                "response_audio_bytes": None,
                "mcp_context": None
            }

            output = await asyncio.to_thread(compiled_aarogya_agent.invoke, state_input)
            response_translated = output.get("response_translated")
            await progress_msg.edit_text(response_translated)
            
            # Value-driven trigger onboarding check
            await check_and_prompt_progressive(patient.telegram_id, update, context)
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
    
    if selection == "media_rx":
        await process_prescription_flow(update, context, media_bytes, None, query=query)
        context.user_data.pop("uploaded_media", None)
        return
        
    # Report flow
    await query.edit_message_text("🔄 Processing document... please wait. This can take a few seconds.")
    
    state_input = {
        "patient_id": patient.id,
        "telegram_id": patient.telegram_id,
        "input_type": "report",
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
        "response_audio_bytes": None,
        "mcp_context": None
    }

    output = await asyncio.to_thread(compiled_aarogya_agent.invoke, state_input)
    response_translated = output.get("response_translated")
    
    await query.edit_message_text(response_translated)
    
    # Clear memory cache
    context.user_data.pop("uploaded_media", None)
    
    # Value-driven trigger onboarding check
    await check_and_prompt_progressive(patient.telegram_id, update, context)

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


# --- MCP Tool Command Handlers ---

async def patient_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /patient <id> — look up patient by UUID via MCP."""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /patient <patient_uuid>")
        return

    patient_id = args[0]
    await update.message.reply_chat_action("typing")
    result = call_mcp_tool("search_patient", {"patient_id": patient_id})

    if "error" in result:
        await update.message.reply_text(f"❌ {result['error']}")
        return

    msg = (
        f"👤 *Patient Details*\n\n"
        f"🆔 ID: `{result['id']}`\n"
        f"📛 Name: {result['name']}\n"
        f"🎂 Age: {result.get('age', 'N/A')}\n"
        f"⚧ Gender: {result.get('gender', 'N/A')}\n"
        f"📱 Phone: {result.get('phone', 'N/A')}\n"
        f"🏘️ Village: {result.get('village', 'N/A')}\n"
        f"⚠️ Risk Score: {result.get('risk_score', 0)}\n"
        f"📊 Risk Level: {result.get('risk_level', 'Low')}\n"
        f"✅ Active: {'Yes' if result.get('is_active') else 'No'}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def risk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /risk <id> — retrieve patient risk assessment via MCP."""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /risk <patient_uuid>")
        return

    patient_id = args[0]
    await update.message.reply_chat_action("typing")
    result = call_mcp_tool("get_patient_risk", {"patient_id": patient_id})

    if "error" in result:
        await update.message.reply_text(f"❌ {result['error']}")
        return

    level = result.get('risk_level', 'Low')
    emoji = '🟢' if level == 'Low' else '🟡' if level == 'Medium' else '🔴'
    factors = result.get('risk_factors', [])
    factors_str = "\n".join([f"  • {f}" for f in factors]) if factors else "  None identified"

    msg = (
        f"{emoji} *Risk Assessment*\n\n"
        f"👤 Patient: {result.get('patient_name', 'Unknown')}\n"
        f"📊 Score: {result.get('risk_score', 0)}/100\n"
        f"⚠️ Level: {level}\n\n"
        f"📋 Risk Factors:\n{factors_str}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def prescriptions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /prescriptions <id> — list patient prescriptions via MCP."""
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /prescriptions <patient_uuid>")
        return

    patient_id = args[0]
    await update.message.reply_chat_action("typing")
    result = call_mcp_tool("get_patient_prescriptions", {"patient_id": patient_id})

    if "error" in result:
        await update.message.reply_text(f"❌ {result['error']}")
        return

    rx_list = result.get('prescriptions', [])
    if not rx_list:
        await update.message.reply_text(f"No prescriptions found for {result.get('patient_name', 'patient')}.")
        return

    header = f"💊 *Prescriptions for {result.get('patient_name', 'Patient')}* ({result.get('total_prescriptions', 0)} total)\n\n"
    entries = []
    for i, rx in enumerate(rx_list[:5], 1):  # Show top 5
        meds = rx.get('medicines', [])
        if isinstance(meds, list) and meds:
            med_names = ", ".join(m.get('name', '?') if isinstance(m, dict) else str(m) for m in meds[:3])
        else:
            med_names = "N/A"
        entries.append(
            f"{i}. 🩺 {rx.get('diagnosis', 'N/A')}\n"
            f"   💊 {med_names}\n"
            f"   📅 {rx.get('issue_date', 'N/A')}"
        )

    await update.message.reply_text(header + "\n\n".join(entries), parse_mode="Markdown")


async def summary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /summary — retrieve platform dashboard summary via MCP."""
    await update.message.reply_chat_action("typing")
    result = call_mcp_tool("get_dashboard_summary")

    if "error" in result:
        await update.message.reply_text(f"❌ {result['error']}")
        return

    msg = (
        f"📊 *AAROGYA Dashboard Summary*\n\n"
        f"👥 Total Patients: {result.get('patients', 0)}\n"
        f"⚠️ Active Alerts: {result.get('alerts', 0)}\n"
        f"💊 Prescriptions: {result.get('prescriptions', 0)}\n"
        f"🏘️ Village Health Score: {result.get('village_health_score', 0)}%"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger reset confirmation."""
    user = update.effective_user
    patient = get_db_patient(user.id)
    if not patient:
        await update.message.reply_text("You do not have an active profile to reset.")
        return
        
    logger.info(f"RESET: Profile reset triggered by user {user.id} ({patient.full_name})")
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Reset", callback_data="reset_yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="reset_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚠️ *Are you sure you want to reset your profile?*\n\n"
        "This will permanently delete your patient record, all prescriptions, reminders, and activity history. This action cannot be undone.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def reset_yes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    logger.info(f"RESET: Confirmed profile reset for user {telegram_id}")
    
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.telegram_id == telegram_id).first()
        if patient:
            # Delete from DB
            db.delete(patient)
            db.commit()
            logger.info(f"RESET: Profile reset completed for user {telegram_id}")
        else:
            logger.warning(f"RESET: Confirmed profile reset but no patient record found for user {telegram_id}")
    except Exception as e:
        logger.exception(f"RESET: Error during profile deletion for user {telegram_id}: {e}")
        db.rollback()
        await query.edit_message_text("❌ Error resetting profile. Please try again.")
        return
    finally:
        db.close()
        
    # Clear conversation memory and onboarding state
    context.user_data.clear()
    
    reset_text = (
        "🗑️ Profile Reset Complete\n\n"
        "Your health profile has been removed.\n\n"
        "Send /start to create a new profile."
    )
    await query.edit_message_text(reset_text)


async def reset_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    logger.info(f"RESET: Profile reset cancelled by user {telegram_id}")
    
    await query.edit_message_text("✅ Reset cancelled. Your profile remains unchanged.")


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
            ONBOARD_GENDER: [CallbackQueryHandler(onboard_gender, pattern="^gender_")],
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
    
    # Profile callbacks
    application.add_handler(CallbackQueryHandler(prompt_village_enter, pattern="^prompt_village_enter$"))
    application.add_handler(CallbackQueryHandler(prompt_village_skip, pattern="^prompt_village_skip$"))
    application.add_handler(CallbackQueryHandler(prompt_details_add, pattern="^prompt_details_add$"))
    application.add_handler(CallbackQueryHandler(prompt_details_skip, pattern="^prompt_details_skip$"))
    application.add_handler(CallbackQueryHandler(blood_group_callback, pattern="^blood_"))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_chat))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_chat))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_upload))
    application.add_handler(CallbackQueryHandler(handle_media_selection, pattern="^media_"))
    application.add_handler(CallbackQueryHandler(handle_compliance_callback, pattern="^(taken|missed)_"))
    
    # Profile command
    application.add_handler(CommandHandler("profile", profile_cmd))
    
    # Reset command
    application.add_handler(CommandHandler("reset", reset_cmd))
    application.add_handler(CallbackQueryHandler(reset_yes_callback, pattern="^reset_yes$"))
    application.add_handler(CallbackQueryHandler(reset_cancel_callback, pattern="^reset_cancel$"))
    
    # MCP command handlers
    application.add_handler(CommandHandler("patient", patient_cmd))
    application.add_handler(CommandHandler("risk", risk_cmd))
    application.add_handler(CommandHandler("prescriptions", prescriptions_cmd))
    application.add_handler(CommandHandler("summary", summary_cmd))
        
    # Print all registered handlers at startup
    logger.info("Registered handlers list:")
    for group, handlers in application.handlers.items():
        logger.info(f"Group {group}: {[type(h).__name__ for h in handlers]}")
        
    # Run Bot
    logger.info("AAROGYA bot handler starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
