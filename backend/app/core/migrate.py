"""Lightweight schema migrations for existing databases (no Alembic)."""
import logging
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger("aarogya.migrate")

MIGRATIONS = [
    "ALTER TABLE patients ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE NOT NULL",
    "ALTER TABLE prescriptions ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE NOT NULL",
    "ALTER TABLE prescriptions ADD COLUMN IF NOT EXISTS telegram_id BIGINT",
    "ALTER TABLE prescriptions ADD COLUMN IF NOT EXISTS diagnosis TEXT",
    "ALTER TABLE lab_reports ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE NOT NULL",
    "ALTER TABLE lab_reports ADD COLUMN IF NOT EXISTS ai_explanation TEXT",
    "ALTER TABLE risk_alerts ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE NOT NULL",
    "ALTER TABLE symptom_logs ADD COLUMN IF NOT EXISTS symptoms TEXT",
    "ALTER TABLE symptom_logs ADD COLUMN IF NOT EXISTS severity VARCHAR(50)",
    "ALTER TABLE symptom_logs ADD COLUMN IF NOT EXISTS recommendation TEXT",
    """CREATE TABLE IF NOT EXISTS activity_logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        activity_type VARCHAR(100) NOT NULL,
        message TEXT NOT NULL,
        is_demo BOOLEAN DEFAULT FALSE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
    )""",
    "ALTER TABLE activity_logs ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE NOT NULL",
    "CREATE INDEX IF NOT EXISTS idx_activity_logs_patient ON activity_logs(patient_id)",
    "CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_patients_demo ON patients(is_demo)",
]


def run_migrations():
    try:
        with engine.connect() as conn:
            for sql in MIGRATIONS:
                conn.execute(text(sql))
            conn.commit()
        logger.info("Database migrations applied successfully.")
    except Exception as e:
        logger.warning(f"Migration warning (may be expected on fresh DB): {e}")
