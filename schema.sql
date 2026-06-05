-- AAROGYA Rural Health Platform - Production PostgreSQL Schema Definition
-- Optimized for clinical compliance, multi-lingual patient interactions, and asynchronous AI agent monitoring.

-- Enable UUID extension for secure, non-sequential unique identifiers.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table (Doctors, Healthcare Workers, Administrators)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('doctor', 'hcw', 'admin', 'system')),
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexing users by role for quick lookups on dashboards.
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 2. Patients Table (Subscribers onboarding via Telegram Bot)
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE, -- Nullable initially if registered via dashboard, but required for bot
    phone VARCHAR(20),
    full_name VARCHAR(100) NOT NULL,
    age INT,
    gender VARCHAR(20),
    village VARCHAR(100),
    sub_center VARCHAR(100),
    assigned_hcw_id UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_doctor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    preferred_language VARCHAR(50) DEFAULT 'english' NOT NULL CHECK (preferred_language IN ('tamil', 'hindi', 'telugu', 'kannada', 'malayalam', 'english')),
    medical_history JSONB DEFAULT '{}'::jsonb NOT NULL, -- Chronic conditions, allergies, baseline parameters
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    risk_score INT DEFAULT 0,
    risk_level VARCHAR(50) DEFAULT 'low',
    risk_factors JSONB DEFAULT '[]'::jsonb,
    is_demo BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indices for patient management filtering by location and coordinators.
CREATE INDEX IF NOT EXISTS idx_patients_assigned_hcw ON patients(assigned_hcw_id);
CREATE INDEX IF NOT EXISTS idx_patients_assigned_doctor ON patients(assigned_doctor_id);
CREATE INDEX IF NOT EXISTS idx_patients_village ON patients(village);
CREATE INDEX IF NOT EXISTS idx_patients_telegram_id ON patients(telegram_id);

-- 3. Prescriptions Table (Uploaded prescription images & clinical analysis logs)
CREATE TABLE IF NOT EXISTS prescriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    raw_image_url TEXT NOT NULL,
    raw_ocr_text TEXT,
    structured_data JSONB DEFAULT '[]'::jsonb NOT NULL, -- Extracted medicine schedules list
    issue_date DATE,
    telegram_id BIGINT,
    diagnosis TEXT,
    is_demo BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_prescriptions_patient ON prescriptions(patient_id);

-- 4. Medicine Reminders Table (Generated schedules from prescriptions)
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    prescription_id UUID REFERENCES prescriptions(id) ON DELETE SET NULL,
    medicine_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(100), -- e.g., "1 tablet", "5ml"
    schedule_time TIME NOT NULL, -- e.g. "08:00:00"
    frequency VARCHAR(50) DEFAULT 'daily' NOT NULL, -- "daily", "alternate_days", "weekly"
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reminders_patient ON reminders(patient_id);
CREATE INDEX IF NOT EXISTS idx_reminders_active ON reminders(is_active);

-- 5. Medicine Compliance Logs Table (Tracks patient actions per reminder)
CREATE TABLE IF NOT EXISTS compliance_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reminder_id UUID NOT NULL REFERENCES reminders(id) ON DELETE CASCADE,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    taken_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL CHECK (status IN ('pending', 'taken', 'missed', 'delayed')),
    response_voice_url TEXT, -- In case patient logs compliance via custom voice feedback
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_compliance_logs_reminder ON compliance_logs(reminder_id);
CREATE INDEX IF NOT EXISTS idx_compliance_logs_status ON compliance_logs(status);
CREATE INDEX IF NOT EXISTS idx_compliance_logs_scheduled ON compliance_logs(scheduled_time);

-- 6. Lab Reports Table (Blood, Urine, and Clinical Reports)
CREATE TABLE IF NOT EXISTS lab_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    file_url TEXT NOT NULL,
    report_type VARCHAR(100),
    raw_ocr_text TEXT,
    extracted_metrics JSONB DEFAULT '{}'::jsonb NOT NULL, -- Metrics parsed: { HbA1c: 8.2, Creatinine: 1.1 }
    summary_local_lang TEXT, -- Patient friendly translated explanation
    ai_explanation TEXT,
    is_demo BOOLEAN DEFAULT FALSE NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lab_reports_patient ON lab_reports(patient_id);

-- 7. Daily Symptom Logs Table (Daily check-ins, telemetry)
CREATE TABLE IF NOT EXISTS symptom_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    answers JSONB DEFAULT '{}'::jsonb NOT NULL, -- Response maps: { fever: "yes", dry_cough: "no" }
    input_voice_url TEXT, -- Store voice check-in if submitted
    transcript TEXT, -- Transcribed voice input (English)
    severity_score INT DEFAULT 0 NOT NULL CHECK (severity_score >= 0 AND severity_score <= 10),
    symptoms TEXT,
    severity VARCHAR(50),
    recommendation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_symptom_logs_patient ON symptom_logs(patient_id);
CREATE INDEX IF NOT EXISTS idx_symptom_logs_created ON symptom_logs(created_at);

-- 8. Risk Alerts Table (System triggered medical escalations)
CREATE TABLE IF NOT EXISTS risk_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    risk_level VARCHAR(50) DEFAULT 'low' NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    source VARCHAR(100) NOT NULL, -- e.g. "symptom_monitor", "compliance_tracker", "report_reader"
    alert_message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'raised' NOT NULL CHECK (status IN ('raised', 'acknowledged', 'resolved')),
    acknowledged_by UUID REFERENCES users(id) ON DELETE SET NULL,
    severity VARCHAR(50),
    reason TEXT,
    recommendation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    is_demo BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_risk_alerts_patient ON risk_alerts(patient_id);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_status ON risk_alerts(status);
CREATE INDEX IF NOT EXISTS idx_risk_alerts_level ON risk_alerts(risk_level);

-- 9. Chat History Table (Logs between patient and Telegram Bot)
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    sender VARCHAR(50) NOT NULL CHECK (sender IN ('patient', 'bot')),
    message TEXT NOT NULL,
    local_language VARCHAR(50) DEFAULT 'english' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chat_history_patient ON chat_history(patient_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created ON chat_history(created_at);

-- 10. Activity Logs Table (Dashboard timeline & audit trail)
CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    is_demo BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_patient ON activity_logs(patient_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_logs_demo ON activity_logs(is_demo);
CREATE INDEX IF NOT EXISTS idx_patients_demo ON patients(is_demo);
