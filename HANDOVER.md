# DEVELOPER HANDOVER DOCUMENT – AAROGYA

Welcome to the **AAROGYA** codebase. This document outlines the system architecture, code modules relationships, and immediate development priorities for the next engineer taking over the platform.

---

## 1. System Architecture & Information Flow

AAROGYA is structured as an event-driven agentic platform:

```text
               +--------------------------------------+
               |      Telegram Client Bot Daemon      |
               |       (telegram_bot/bot/main.py)     |
               +------------------+-------------------+
                                  |
                           (API Requests)
                                  |
                                  v
+------------------+   +----------+-----------+   +-------------------+
|  Celery Workers  |<--| FastAPI Core Gateway |-->|  Next.js Frontend |
|  (Task Queues)   |   |   (backend/app/)     |   |    (frontend/)    |
+--------+---------+   +----------+-----------+   +---------+---------+
         |                        |                         |
         | (reminders/remits)     | (SQLAlchemy / JWT)      | (Live API Fetch)
         v                        v                         v
+---------------------------------------------------------------------+
|                     PostgreSQL Database Engine                      |
|                            (schema.sql)                             |
+---------------------------------------------------------------------+
```

### Data Pipeline
1. **Onboarding**: Patient registers via Telegram bot. The bot writes a record to the `patients` table.
2. **Prescription Parsing**: Patient uploads a prescription image -> Telegram bot sends bytes to `/prescriptions/upload` -> FastAPI routes it to the **LangGraph Agent** -> Gemini extracts structured medicines -> records are saved to the `prescriptions` table -> medication reminders are generated and written to the `reminders` table.
3. **Medication Reminders**: Celery Beat runs hourly -> finds reminders matching the current hour -> inserts pending compliance checks to `compliance_logs` -> pushes inline check-in cards (Taken / Missed) to the patient on Telegram.
4. **Symptom Telemetry**: Patient interacts via text/voice check-ins -> Whisper transcribes audio -> LangGraph rates severity -> writes to `symptom_logs` -> risk detector flags warnings -> writes to `risk_alerts` table -> worker alerts assigned ANM health workers.
5. **Dashboard Audits**: Doctors view live statistics from the `/dashboard/summary` and `/patients` endpoints. HCWs view checklist alerts and resolve them directly.

---

## 2. Key Code Areas & Hand-off Notes

### LangGraph Agent Engine ([graph.py](file:///c:/Users/sandh/Downloads/Telegram%20Ai/backend/app/agents/graph.py))
- **Node Classification**: `classifier_node` routes inputs based on whether they contain text, voice, prescriptions, or blood reports.
- **Biomarker Scanners**: `prescription_reader_node` and `report_explainer_node` invoke Gemini Vision prompts to return structured JSON.
- **Safety Detector**: `risk_detector_node` evaluates clinical parameters. If severity is high (>=5) or critical (>=8), it immediately writes an alert to the `risk_alerts` table.
- **Responder**: `responder_node` handles translations to local scripts (Hindi, Tamil, etc.) and generates text-to-speech voice payloads.

### Telegram Polling Bot ([main.py](file:///c:/Users/sandh/Downloads/Telegram%20Ai/telegram_bot/bot/main.py))
- Extends `ConversationHandler` to manage patient onboarding (name, village, preferred language selection).
- Implements callback query handlers for inline compliance buttons (Taken vs Missed) to update database logs.
- Direct database calls use `SessionLocal()` instances inside handlers.

---

## 3. High Priority Development Tasks (Roadmap)

To move this system from Hackathon-ready to a production MVP, complete the following tasks:

### Task 1: Complete Frontend Auth & Navigation guards
- **Problem**: Next.js assumes a pre-logged-in physician (uses fallback headers).
- **Solution**: 
  - Create a login form (`src/app/login/page.tsx`).
  - Send POST requests to `/auth/login` to retrieve JWT access tokens.
  - Store tokens in HTTP-only cookies and configure Next.js middleware guards to block unauthenticated requests to `/dashboard`.

### Task 2: Implement Real S3 Image Uploads
- **Problem**: Image bytes are processed in memory and DB tables store placeholder S3 paths.
- **Solution**:
  - Add a file storage utility using `boto3`.
  - Inside `prescription_reader_node` and `report_explainer_node` ([graph.py](file:///c:/Users/sandh/Downloads/Telegram%20Ai/backend/app/agents/graph.py)), upload incoming bytes to your AWS S3 bucket and save the resulting S3 URL in the database.

### Task 3: Hook up Twilio SMS Gateway
- **Problem**: Celery worker alerts are printed to the console rather than sent to the HCW.
- **Solution**:
  - Integrate a Twilio client wrapper inside `celery_worker.py`.
  - Retrieve the assigned HCW phone number from the database and send an SMS notification whenever a critical risk alert is raised.

### Task 4: Setup Database Migrations
- **Problem**: Changing database schemas requires resetting PostgreSQL tables.
- **Solution**:
  - Run `alembic init alembic` in the backend directory.
  - Configure `env.py` to import SQLAlchemy models (`Base.metadata`).
  - Create initial migration scripts to support schema version tracking.
