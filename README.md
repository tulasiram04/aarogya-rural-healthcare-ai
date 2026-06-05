# 🌿 AAROGYA

**AI-Powered Rural Healthcare Companion**

AAROGYA is an agentic rural healthcare platform that connects patients in remote villages with doctors and healthcare workers (HCWs) through Telegram, AI-powered clinical tools, and a real-time web dashboard.

Patients interact via **Telegram** (voice, text, prescription photos, lab reports). Doctors and HCWs monitor compliance, risk alerts, and village health trends through a **Next.js Clinical Command Center** backed by **FastAPI**, **PostgreSQL**, **Redis/Celery**, and **Google Gemini 2.5 Flash**.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Environment Variables](#environment-variables)
- [Access URLs](#access-urls)
- [Demo Credentials](#demo-credentials)
- [Hackathon Demo Mode](#hackathon-demo-mode)
- [Telegram Bot Usage](#telegram-bot-usage)
- [Dashboard Guide](#dashboard-guide)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Local Development (Without Docker)](#local-development-without-docker)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Patient (Telegram Bot)
- **Telegram-only registration** — patients are added to the database exclusively via the bot (`/start`). Manual dashboard/API patient creation is disabled.
- Portal shows only patients with a valid `telegram_id` from bot onboarding (Real Data filter).
- Prescription photo upload → AI OCR → medicine extraction → reminder scheduling
- Lab report upload → biomarker parsing → patient-friendly explanation
- Daily symptom check-ins via text or voice
- Voice-based rural health assistant with AI response in the same language
- Medication compliance reminders with Taken / Missed inline buttons

### Doctor / HCW (Web Dashboard)
- **Clinical Command Center** — live metrics, village health score, AI executive insights
- **Patient Directory** — search, filter, full clinical profiles
- **Doctor Copilot** — AI recommendations, diagnosis, follow-up, lab tests, medication review
- **Predictive Risk Score** (0–100) with contributors and circular gauge
- **Prescription & Lab Report** viewers with OCR-extracted data
- **Risk Alerts** queue with acknowledge / resolve workflow
- **Activity Feed** — real-time timeline of patient events
- **HCW Checklist** — mobile-friendly visit task list from active alerts
- **Voice Assistant Widget** — record symptoms in regional languages
- **Demo Guide** — 10-step hackathon walkthrough timeline

### Platform
- Demo / Real data isolation (`is_demo` flag + data filters)
- Apple-style emoji rendering globally (twemoji)
- Light-mode healthcare UI (Apple Health + Google Health inspired)
- Gemini resiliency — workflows continue even if AI is temporarily unavailable
- Role-based access (Doctor, HCW, Admin)

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Telegram Bot │────▶│   FastAPI API    │◀────│  Next.js        │
│  (Patients)   │     │   (Port 8000)    │     │  Dashboard      │
└────────┬────────┘     └────────┬─────────┘     │  (Port 3000)    │
         │                       │               └─────────────────┘
         │              ┌────────┴────────┐
         │              │                 │
         ▼              ▼                 ▼
   ┌──────────┐   ┌──────────┐    ┌──────────────┐
   │PostgreSQL│   │  Redis   │    │ Celery Worker│
   │  (5432)  │   │  (6379)  │    │  + Beat      │
   └──────────┘   └──────────┘    └──────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Gemini 2.5   │
                  │ Flash (AI)   │
                  └──────────────┘
```

**AI Pipeline (LangGraph):**

```
Patient Input (text / voice / image)
        ↓
   Classifier Node
        ↓
┌───────┼───────┬──────────┐
↓       ↓       ↓          ↓
Rx OCR  Report  Symptom   Chat
Reader  Explainer Monitor Flow
        ↓
   Risk Detector → Responder → Telegram / Dashboard
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend API | FastAPI, Python 3.11, Uvicorn |
| Database | PostgreSQL 15 |
| Cache / Queue | Redis 7, Celery 5 |
| AI | Google Gemini 2.5 Flash, LangGraph |
| Bot | python-telegram-bot 21 |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| UI | Framer Motion, Lucide Icons, Twemoji (Apple) |
| Auth | JWT (Bearer tokens) |
| Containers | Docker Compose |

---

## Project Structure

```
Telegram Ai/
├── README.md                 # This file
├── docker-compose.yml        # Full stack orchestration
├── schema.sql                # PostgreSQL DDL (auto-runs on first DB init)
├── seed_demo_data.py         # Hackathon demo dataset seeder
├── .env.example              # Environment template
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py           # FastAPI entry point
│       ├── api/              # REST routers (auth, patients, dashboard, …)
│       ├── agents/           # LangGraph state machine
│       ├── core/             # Config, DB, security, migrations
│       ├── models/           # SQLAlchemy ORM
│       ├── schemas/          # Pydantic DTOs
│       ├── services/         # Gemini, OCR, voice, risk score, demo data
│       └── tasks/            # Celery worker & beat schedules
│
├── telegram_bot/
│   ├── Dockerfile
│   └── bot/
│       └── main.py           # Telegram polling bot
│
├── frontend/
│   ├── package.json
│   └── src/
│       ├── app/              # Next.js App Router pages
│       ├── components/       # EmojiProvider, Toast, DataFilterBar
│       └── lib/              # API client, data filter context
│
└── uploads/                  # Prescription & report file storage
    ├── prescriptions/
    └── reports/
```

---

## Prerequisites

### Docker (Recommended)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows: enable WSL2)
- 8 GB RAM minimum
- Ports available: **3000**, **5432**, **6379**, **8000**

### API Keys (Required for full AI features)
1. **Telegram Bot Token** — create via [@BotFather](https://t.me/BotFather) on Telegram
2. **Gemini API Key** — get from [Google AI Studio](https://aistudio.google.com/)

---

## Quick Start (Docker)

### 1. Clone and configure

```bash
cd "Telegram Ai"
cp .env.example .env
```

Edit `.env` and set your `TELEGRAM_BOT_TOKEN` and `GEMINI_API_KEY`.

> **Note:** `docker-compose.yml` also reads env vars directly. For production, move all secrets into `.env` only.

### 2. Start the full stack

```bash
docker compose up --build -d
```

This starts **7 services**:

| Container | Service | Description |
|-----------|---------|-------------|
| `aarogya_db` | PostgreSQL | Database |
| `aarogya_redis` | Redis | Celery broker |
| `aarogya_api` | FastAPI | REST API gateway |
| `aarogya_worker` | Celery Worker | Reminder scanner & tasks |
| `aarogya_beat` | Celery Beat | Cron scheduler |
| `aarogya_bot` | Telegram Bot | Patient-facing bot |
| `aarogya_frontend` | Next.js | Doctor/HCW dashboard |

### 3. Verify all services are running

```bash
docker compose ps
```

Expected: all containers show `Up` status.

### 4. Check health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","service":"AAROGYA","version":"1.0.0"}
```

### 5. Load hackathon demo data (optional)

1. Open **http://localhost:3000/login**
2. Login as **Admin** (see credentials below)
3. Click **🚀 Load Hackathon Demo** on the dashboard

Or via API:

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"9876543200","password":"admin123"}'

# Seed demo (use token from login response)
curl -X POST http://localhost:8000/api/v1/dashboard/seed_demo \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. Stop the stack

```bash
docker compose down
```

To reset the database completely:

```bash
docker compose down -v
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | `openssl rand -hex 32` |
| `POSTGRES_SERVER` | DB host | `db` (Docker) / `localhost` (local) |
| `POSTGRES_USER` | DB user | `postgres` |
| `POSTGRES_PASSWORD` | DB password | `postgres` |
| `POSTGRES_DB` | Database name | `aarogya` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | `123456:ABC...` |
| `GEMINI_API_KEY` | Google AI Studio key | `AI...` |
| `NEXT_PUBLIC_API_URL` | Frontend API base URL | `http://localhost:8000/api/v1` |

---

## Access URLs

| Service | URL |
|---------|-----|
| **Dashboard (Login)** | http://localhost:3000/login |
| **Dashboard Overview** | http://localhost:3000/dashboard |
| **Patient Directory** | http://localhost:3000/dashboard/patients |
| **Demo Guide** | http://localhost:3000/dashboard/demo-guide |
| **API Swagger Docs** | http://localhost:8000/docs |
| **API ReDoc** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/health |
| **Telegram Bot** | Search your bot username in Telegram → `/start` |

---

## Demo Credentials

Created automatically by the demo seeder:

| Role | Phone | Password |
|------|-------|----------|
| **Admin** | `9876543200` | `admin123` |
| **Doctor** | `9876543210` | `doctor123` |
| **HCW** | `9876543211` | `hcw123` |

The login page also has quick-fill buttons for these credentials.

---

## Hackathon Demo Mode

AAROGYA separates **real patient data** from **demo data** using an `is_demo` flag on patients, prescriptions, lab reports, risk alerts, and activity logs.

### Dashboard controls (Admin only)

| Button | Action |
|--------|--------|
| **🚀 Load Hackathon Demo** | Removes old demo records → seeds 10 patients with prescriptions, labs, alerts, compliance logs |
| **🗑 Clean Demo Data** | Deletes demo records only; real patients are preserved |

### Data filter (header bar)

| Filter | Shows |
|--------|-------|
| **All Data** | Everything |
| **Real Data** | Production / Telegram-registered patients only |
| **Demo Data** | Hackathon demo dataset only |

### Demo dataset includes

- 1 Doctor, 1 HCW, 1 Admin
- 10 patients across 3 villages (Hasanpur, Bhondsi, Manesar)
- 5 prescriptions with active medicine reminders
- 5 lab reports with parsed biomarkers
- 7 symptom check-in logs
- 5 active risk alerts
- 7-day compliance history
- Predictive risk scores recalculated for all demo patients

---

## Telegram Bot Usage

### Setup
1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Set `TELEGRAM_BOT_TOKEN` in your environment
3. Restart the bot container: `docker compose restart telegram_bot`

### Patient flow
1. Send `/start` to your bot
2. Complete onboarding: **Name → Age → Language**
3. Use the inline menu:
   - **Daily Check-in** — report symptoms
   - **Upload Prescription** — send a photo of a prescription card
   - **Upload Lab Report** — send a photo of a lab report
4. Send **voice notes** for symptom reporting (auto-transcribed + AI reply)
5. Respond to **medication reminders** with Taken / Missed buttons

### Supported languages
Tamil · Hindi · Telugu · Kannada · Malayalam · English

---

## Dashboard Guide

### Clinical Command Center (`/dashboard`)
- Welcome header with AI assistant status
- 6 metric cards: Patients, Prescriptions, Lab Reports, Risk Alerts, Compliance, Village Health Score
- Voice Assistant widget (6 languages)
- AI Executive Insights (Gemini-generated village summary)
- Active alerts queue, activity feed, village compliance trends
- Command center widgets: top diseases, risk villages, active patients, missed medicines, patients requiring attention

### Patient Profile (`/dashboard/patients/[id]`)
- Patient header with avatar, village, compliance %, risk score gauge
- **Doctor Copilot** — 6 AI recommendation categories
- AI Clinical Summary
- Prescriptions, reminders, lab reports, symptom logs
- Medication adherence analytics
- Chronological timeline

### Other pages
| Page | Path | Purpose |
|------|------|---------|
| Patients | `/dashboard/patients` | Searchable patient directory |
| Prescriptions | `/dashboard/prescriptions` | All uploaded prescriptions |
| Lab Reports | `/dashboard/reports` | All parsed lab reports |
| Risk Alerts | `/dashboard/alerts` | Active clinical alerts |
| HCW Checklist | `/dashboard/hcw` | Field visit task list |
| Demo Guide | `/dashboard/demo-guide` | 10-step hackathon timeline |

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

Authentication: `Authorization: Bearer <JWT_TOKEN>`

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register doctor/HCW |
| POST | `/auth/login` | Login (returns JWT) |
| GET | `/auth/me` | Current user profile |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/summary?data_filter=all\|real\|demo` | Aggregated metrics |
| POST | `/dashboard/seed_demo` | Load hackathon demo (admin) |
| DELETE | `/dashboard/clean_demo` | Remove demo data (admin) |

### Patients
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/patients/?data_filter=` | List patients |
| GET | `/patients/{id}` | Full clinical profile |
| GET | `/patients/{id}/copilot` | Doctor Copilot AI analysis |
| POST | `/patients/` | Register patient |
| PUT | `/patients/{id}` | Update patient |

### Clinical Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/prescriptions` | List / upload prescriptions |
| GET/POST | `/reports` | List / upload lab reports |
| GET | `/alerts/` | Active risk alerts |
| PATCH | `/alerts/{id}/acknowledge` | Acknowledge alert |
| PATCH | `/alerts/{id}/resolve` | Resolve alert |
| GET | `/activity` | Activity feed |
| GET | `/reminders/patient/{id}` | Patient reminders |
| GET | `/reminders/compliance/stats/{id}` | Compliance stats |

### Voice Assistant
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/assistant/voice` | Upload audio → transcript + AI response + TTS |

Interactive docs: **http://localhost:8000/docs**

---

## Database Schema

PostgreSQL with UUID primary keys. Tables:

| Table | Purpose |
|-------|---------|
| `users` | Doctors, HCWs, admins |
| `patients` | Patient demographics & risk scores |
| `prescriptions` | OCR-extracted prescription data |
| `reminders` | Medicine schedules |
| `compliance_logs` | Taken / missed / pending doses |
| `lab_reports` | Parsed biomarker metrics |
| `symptom_logs` | Daily check-in records |
| `risk_alerts` | Clinical escalation alerts |
| `activity_logs` | Dashboard timeline events |
| `chat_history` | Telegram conversation logs |

Schema is applied via:
1. `schema.sql` on first Docker DB init
2. Auto-migrations in `backend/app/core/migrate.py` on API startup

---

## Local Development (Without Docker)

### 1. Database
Install PostgreSQL 15, create database `aarogya`, run `schema.sql`.

### 2. Redis
Install and start Redis on port 6379.

### 3. Backend
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Celery (separate terminals)
```bash
cd backend
celery -A app.tasks.celery_worker.celery_app worker --loglevel=info -P threads
celery -A app.tasks.celery_worker.celery_app beat --loglevel=info
```

### 5. Telegram Bot
```bash
cd telegram_bot
python bot/main.py
```

### 6. Frontend
```bash
cd frontend
npm install
npm run dev
```

Set in `.env`:
```
POSTGRES_SERVER=localhost
REDIS_URL=redis://localhost:6379/0
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Troubleshooting

### Containers not starting
```bash
docker compose logs api          # API errors
docker compose logs telegram_bot # Bot errors
docker compose logs frontend     # Frontend errors
```

### Database schema out of date
```bash
docker compose down -v    # WARNING: deletes all data
docker compose up --build -d
```

### Frontend can't reach API
Ensure `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` and the API container is running on port 8000.

### Telegram bot not responding
1. Verify `TELEGRAM_BOT_TOKEN` is correct
2. Check logs: `docker compose logs telegram_bot -f`
3. Restart: `docker compose restart telegram_bot`

### Gemini AI not working
- Verify `GEMINI_API_KEY` in environment
- Workflows continue with graceful fallback messages if AI is unavailable
- Check logs: `docker compose logs api | grep gemini`

### Demo seed fails
- Login as admin (`9876543200` / `admin123`)
- Ensure API container has `seed_demo_data.py` mounted (see `docker-compose.yml`)
- Rebuild: `docker compose build api && docker compose up -d api`

### Frontend 500 / MODULE_NOT_FOUND in Docker

The dev container mounts `./frontend` as a volume. If you see 500 errors after pulling new code, clear the stale build cache:

```bash
# Windows PowerShell
Remove-Item -Recurse -Force frontend\.next
docker compose restart frontend
```

Wait ~30 seconds for Next.js to recompile, then open http://localhost:3000/login

### Port already in use
```bash
# Find process on port 8000 (Windows PowerShell)
netstat -ano | findstr :8000
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following existing code conventions
4. Test with `docker compose up --build` and `npm run build` in frontend
5. Submit a pull request

---

## License

This project was built for rural healthcare hackathon demonstration. Contact the project maintainers for licensing terms.

---

<p align="center">
  <strong>🌿 AAROGYA</strong><br>
  <em>AI-Powered Rural Healthcare Companion</em><br><br>
</p>
