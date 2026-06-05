import os
import logging
import requests
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timezone, time
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.patient import Patient
from app.models.medical import Reminder, ComplianceLog
from app.models.logs import RiskAlert
from app.models.user import User

logger = logging.getLogger("aarogya.celery")

# Initialize Celery app
celery_app = Celery(
    "aarogya_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Optional celery configurations
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# --- Async Celery Tasks ---

@celery_app.task(name="tasks.send_medicine_reminders")
def send_medicine_reminders():
    """
    Scans the database for medicine reminders matching the current hour.
    Spawns pending ComplianceLogs, and pushes cards with Taken/Missed actions to the patient's Telegram Bot.
    """
    logger.info("Celery task: Scanning schedules for due reminders...")
    db: Session = SessionLocal()
    current_time = datetime.now(timezone.utc)
    current_hour = current_time.hour
    
    try:
        # Fetch active reminders (simplifying timing match for demo production logic: fetch matches for the hour)
        reminders = db.query(Reminder).filter(
            Reminder.is_active == True
        ).all()
        
        for rem in reminders:
            # Check if reminder schedule time matches active slots (within the hour)
            if rem.schedule_time.hour == current_hour:
                # 1. Create a compliance log entry
                log_entry = ComplianceLog(
                    reminder_id=rem.id,
                    scheduled_time=current_time,
                    status="pending"
                )
                db.add(log_entry)
                db.commit()
                db.refresh(log_entry)
                
                # 2. Push message to patient's Telegram Client
                patient = rem.patient
                if patient.telegram_id:
                    push_telegram_reminder(patient.telegram_id, rem, log_entry.id)
                    
    except Exception as e:
        logger.error(f"Error during medicine reminders scan: {str(e)}")
        db.rollback()
    finally:
        db.close()


def push_telegram_reminder(telegram_id: int, reminder: Reminder, log_id: str):
    """Hits the Telegram REST API endpoint directly to post medicine inline action buttons."""
    token = settings.TELEGRAM_BOT_TOKEN
    if token == "PLACEHOLDER_TOKEN":
        logger.warning(f"Telegram Bot Token placeholder. Medicine remind push skipped for patient ID {telegram_id}.")
        return

    # Language localizations
    lang = reminder.patient.preferred_language
    
    text_taken = "💊 Taken"
    text_missed = "❌ Missed"
    prompt_text = f"Time to take your medicine:\n\n*Medication:* {reminder.medicine_name}\n*Dosage:* {reminder.dosage or 'As prescribed'}"

    if lang == "hindi":
        text_taken = " ले लिया"
        text_missed = " छूट गया"
        prompt_text = f"दवा लेने का समय:\n\n*दवा:* {reminder.medicine_name}\n*मात्रा:* {reminder.dosage or 'निर्देशानुसार'}"
    elif lang == "tamil":
        text_taken = "சாப்பிட்டேன்"
        text_missed = "தவறவிட்டேன்"
        prompt_text = f"மருந்து உட்கொள்ளும் நேரம்:\n\n*மருந்து:* {reminder.medicine_name}\n*அளவு:* {reminder.dosage or 'பரிந்துரைக்கப்பட்டபடி'}"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": prompt_text,
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": text_taken, "callback_data": f"taken_{log_id}"},
                    {"text": text_missed, "callback_data": f"missed_{log_id}"}
                ]
            ]
        }
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        logger.info(f"Compliance push sent to Telegram ID {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to post reminder to Telegram: {str(e)}")


@celery_app.task(name="tasks.notify_hcw_escalation")
def notify_hcw_escalation(alert_id: str):
    """
    Triggers an SMS or Telegram notice to a Healthcare Worker (HCW)
    indicating that one of their assigned patients is in a CRITICAL or HIGH risk state.
    """
    db: Session = SessionLocal()
    try:
        alert = db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
        if not alert or alert.status != "raised":
            return
            
        patient = alert.patient
        hcw = patient.assigned_hcw
        
        if hcw and hcw.phone:
            message = (
                f"🚨 AAROGYA ALERT 🚨\n"
                f"Patient: {patient.full_name} ({patient.village})\n"
                f"Risk: {alert.risk_level.upper()}\n"
                f"Details: {alert.alert_message}\n"
                f"Please conduct an immediate home checkup."
            )
            # In production: hit twilio, textlocal, or SMS gateway.
            # For this architecture, we push a warning log representation.
            logger.warning(f"SMS OUTGOING TO HCW ({hcw.full_name} - {hcw.phone}):\n{message}")
            
    except Exception as e:
        logger.error(f"HCW escalation notification task failed: {str(e)}")
    finally:
        db.close()


# --- Schedule configurations using Celery Beat ---

celery_app.conf.beat_schedule = {
    "scan-medicine-schedules-every-hour": {
        "task": "tasks.send_medicine_reminders",
        "schedule": crontab(minute=0), # every hour on the hour
    }
}
