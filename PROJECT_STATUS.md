# PROJECT STATUS – AAROGYA: The Village Doctor Agent

This document is a hand-off reference for developers continuing the development, testing, and deployment of the **AAROGYA** Agentic Rural Healthcare Platform.

---

## 1. Project Overview & Completion Metrics

AAROGYA is an AI-driven rural healthcare platform designed to run on low bandwidth. It integrates a **Telegram Bot** (patient onboarding, voice chat, OCR prescriptions, medicine check-ins) with a **Next.js Dashboard** (for Doctors and Healthcare Workers to track compliance and address clinical risk alerts) backed by a **FastAPI** server and **Celery** scheduling queues.

### Completion Scores
* **Backend API Gateway**: `90%` (routes, validations, database connectors, and JWT logic are complete)
* **AI Agent Graph**: `90%` (StateGraph nodes, Vision OCR, severity rating, and translation wrappers are complete)
* **Telegram Bot Client**: `95%` (async handlers, callback buttons, voice transcriptions, and image categories menus are complete)
* **Database Layer**: `80%` (SQL schema and indices are complete; migrations are missing)
* **Deployment Orchestrator**: `85%` (Docker composition is ready; proxy layer is missing)
* **Frontend Dashboard UI**: `40%` (structure, design styling, and responsive checklists are complete; API hooks are integrated, but authentication logins and calendar grids are missing)
* **Overall Completion Score**: **80%**

---

## 2. Completed, Partially Completed, & Missing Modules

### Completed Modules
* **Authentication Server** ([auth.py](file:///c:/Users/sandh/Downloads/Telegram%20Ai/backend/app/api/auth.py)): Hashing, logins, registration, and dependency checks.
* **Patient Management** ([patients.py](file:///c:/Users/sandh/Downloads/Telegram%20Ai/backend/app/api/patients.py)): Demographics registers, RBAC lists filters, and detailed diagnostic aggregators.
* **LangGraph Orchestrator** ([graph.py](file:///c:/Users/sandh/Downloads/Telegram%20Ai/backend/app/agents/graph.py)): Multi-agent state machine routing inputs through OCR, clinical severity check, risk detectors, and localized translators.
* **OCR Service** ([ocr.py](file:///c:/Users/sandh/Downloads/Telegram%20Ai/backend/app/services/ocr.py)): Multi-modal image parsing for medicine schedules and blood panels.
* **Voice Service** ([voice.py](file:///c:/Users/sandh/Downloads/Telegram%20Ai/backend/app/services/voice.py)): Audio transcription and gTTS speech synthesis.
* **Telegram Bot** ([main.py](file:///c:/Users/sandh/Downloads/Telegram%20Ai/telegram_bot/bot/main.py)): Multi-language onboarding, voice notes handling, callback updates.
* **Hourly Scheduler** ([celery_worker.py](file:///c:/Users/sandh/Downloads/Telegram%20Ai/backend/app/tasks/celery_worker.py)): Hourly cron scanner, DB compliance logs injector, and direct Telegram reminders pusher.

### Partially Completed Modules
* **S3 Storage Integrations**: Config parameters are initialized in [config.py](file:///c:/Users/sandh/Downloads/Telegram%20Ai/backend/app/core/config.py), but actual boto3 calls are mocked. Files are processed directly in-memory, and DB columns store placeholder S3 URLs.
* **SMS Gateway Escalar**: Celery worker logs alert escalations to the console but does not yet connect to an active provider API (e.g. Twilio).

### Missing Modules
* **Frontend User Login Screen**: Dashboard assumes doctor is pre-logged-in (via bypass authorization headers). Login view and cookie token caching are missing.
* **Database Migration Engine**: Alembic migrations directory is missing.
* **API Rate Limiter**: Rate-limiting middlewares are missing.
* **IndicTrans2 Local Binding**: Uses Gemini translation prompts. A local GPU container binding for true offline environments is missing.

---

## 3. Production Folder Structure

```text
aarogya/
├── backend/                       # FastAPI Server & Workers
│   ├── app/
│   │   ├── api/                   # Router endpoints (Auth, Patients, Alerts)
│   │   ├── core/                  # Configurations, DB connectors, security
│   │   ├── models/                # SQLAlchemy database models
│   │   ├── schemas/               # Pydantic validation models
│   │   ├── services/              # AI adapters (Gemini, OCR, Voice, Translation)
│   │   ├── agents/                # LangGraph state machine & nodes
│   │   ├── tasks/                 # Celery worker schedules and tasks
│   │   └── main.py                # FastAPI bootstrapper
│   ├── requirements.txt
│   └── Dockerfile
├── telegram_bot/                  # Polling bot client
│   ├── bot/
│   │   └── main.py                # Bot runner
│   └── Dockerfile
├── frontend/                      # Next.js Dashboard UI
│   ├── src/
│   │   ├── app/                   # App Router pages (Overview, Patients, HCW checklist)
│   │   ├── lib/                   # Centralized API client (api.ts)
│   │   └── globals.css            # Stylesheets & CSS design tokens
│   ├── package.json
│   └── tsconfig.json
├── schema.sql                     # PostgreSQL Database DDL
└── docker-compose.yml             # System orchestrator compose file
```

---

## 4. Database Schema Summary

The database uses PostgreSQL with UUID primary keys and performance-optimized indices:

* `users`: Medical worker profiles (Doctor, HCW, Admin) with hashed passwords.
* `patients`: Onboarded users via Telegram bot, assigned workers, villages, and chronic history JSON.
* `prescriptions`: Image files references, raw OCR, and structured medicine JSON.
* `reminders`: Dosage regimes (time, frequency, start/end dates) linked to prescriptions.
* `compliance_logs`: Tracks dosage responses (taken, missed, delayed) matching scheduled times.
* `lab_reports`: File URLs, blood panel biomarker JSON, and translated summaries.
* `symptom_logs`: Answers to daily check-ins and clinical severity ratings.
* `risk_alerts`: Critical alerts (raised, acknowledged, resolved) pointing to assigned workers.
* `chat_history`: Logs dialogue interactions in local regional scripts.

---

## 5. API Endpoints Summary

All routes are mounted under `/api/v1` and require Bearer JWT authorization (except Auth registration/login):

* **Auth**:
  * `POST /auth/register`: Create a new Doctor/HCW profile.
  * `POST /auth/login`: Authenticate credentials, returns access token.
  * `GET /auth/me`: Retrieve active profile data.
* **Patients**:
  * `POST /patients/`: Register a new patient.
  * `GET /patients/`: List assigned patients (filtered dynamically by role).
  * `GET /patients/{id}`: Detailed medical chart dossier (reminders, reports, symptoms, active alerts).
  * `PUT /patients/{id}`: Modify demographics.
* **Uploads**:
  * `POST /prescriptions/upload`: Process prescription image bytes, parses medicines via LangGraph, and spawns reminders.
  * `POST /reports/upload`: Process blood tests, extracts biomarkers, and drafts summaries.
* **Reminders**:
  * `GET /reminders/patient/{patient_id}`: Get active schedules.
  * `POST /reminders/compliance/{log_id}`: Log reminder updates (taken/missed).
  * `GET /reminders/compliance/stats/{patient_id}`: Calculate overall patient compliance rate.
* **Alerts**:
  * `GET /alerts/`: List unresolved risk alarms (filtered dynamically by worker assignments).
  * `PATCH /alerts/{alert_id}/acknowledge`: Mark alert status as acknowledged.
  * `PATCH /alerts/{alert_id}/resolve`: Mark alert status as resolved.
* **Dashboard**:
  * `GET /dashboard/summary`: Consolidated statistics (active alarms count, average compliance rate by village).

---

## 6. Local Setup Requirements

### System Pre-requisites
1. **Docker Desktop** (with WSL2 backend enabled).
2. **Node.js** (v18+) & **NPM** (v9+).
3. **Python** (v3.11+) - optional (if running outside Docker).
4. **Git** bash.

### Setup Instructions
1. Clone the project and configure environment secrets:
   Create a `.env` file inside the root directory or configure them in [docker-compose.yml](file:///c:/Users/sandh/Downloads/Telegram%20Ai/docker-compose.yml):
   * `GEMINI_API_KEY`: API key from Google AI Studio.
   * `TELEGRAM_BOT_TOKEN`: Token from Telegram BotFather.
2. Spin up the containers:
   ```bash
   docker-compose up --build
   ```
3. Initialize test datasets:
   - Access Swagger API docs at `http://localhost:8000/docs`.
   - Call `/auth/register` to create a doctor.
   - Register a patient using `/patients/`.
   - Access the bot on Telegram, select onboarding languages, and test voice transcription or prescription image category routing.
4. Access the UI:
   - Doctor dashboard: `http://localhost:3000/dashboard`.
   - HCW mobile checklist companion: `http://localhost:3000/dashboard/hcw`.

---

## 7. Known Issues & Workarounds

* **S3 Bucket Fails**: If S3 endpoints are not configured, image uploads still succeed. Bytes are parsed directly in-memory, but database files columns will store placeholder S3 paths.
* **Gemini Offline Mock**: If the `GEMINI_API_KEY` environment variable is not configured, AI services fall back to local test objects for prescriptions, blood reports, and symptom check-ins.
* **Alembic DB Configs**: Running `alembic upgrade head` will fail because the migrations directory has not been initialized. If you modify the DB schemas, you must drop the PostgreSQL docker volume (`docker-compose down -v`) to force the database to reload [schema.sql](file:///c:/Users/sandh/Downloads/Telegram%20Ai/schema.sql) on startup.

---

## 8. How to Continue Development (Roadmap)

1. **Authentication Screens**: Implement login page and route guards inside the Next.js frontend using JWT authorization headers.
2. **Boto3 S3 Uploader**: Add real S3 upload helpers in `backend/app/services/` to save prescription/report files to an AWS S3 bucket.
3. **Twilio SMS Connector**: Replace the logs in `celery_worker.py:notify_hcw_escalation` with a Twilio SMS client wrapper.
4. **Alembic Setup**: Run `alembic init` inside the backend directory to track database schema modifications.
