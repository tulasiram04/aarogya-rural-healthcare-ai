# SETUP GUIDE – AAROGYA

This guide describes how to configure and run the complete AAROGYA system locally. Since the platform has multi-container dependencies (PostgreSQL, Redis, Celery, Node.js), you can run it either via **Docker Compose** (recommended) or **locally on your host machine**.

---

## Pre-requisites & Credentials Setup

Before starting, copy the `.env.example` file to `.env` in the root folder:
```bash
cp .env.example .env
```
Open `.env` and fill in the following keys:
1. **`TELEGRAM_BOT_TOKEN`**: Create a new bot on Telegram using `@BotFather` and retrieve the token.
2. **`GEMINI_API_KEY`**: Register for a developer account at [Google AI Studio](https://aistudio.google.com/) and create an API key.

---

## Option A: Docker Compose Deployment (Recommended)

This compiles and runs the entire stack inside containerized networks automatically.

### Requirements:
* Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) (ensure WSL2 is enabled).

### Steps:
1. Start the Docker services:
   ```bash
   docker-compose up --build
   ```
2. On boot, Postgres will automatically execute and seed tables from the [schema.sql](file:///c:/Users/sandh/Downloads/Telegram%20Ai/schema.sql) file.
3. Access the services:
   * **FastAPI Backend Gateway**: `http://localhost:8000/docs` (Swagger Interactive Playground).
   * **Doctor Command Dashboard**: `http://localhost:3000/dashboard` (Next.js client interface).
   * **HCW Visit Companion**: `http://localhost:3000/dashboard/hcw` (Mobile checklist view).
   * **Telegram Bot**: Open your Telegram client, search for your bot's username, and press `/start`.

---

## Option B: Local Windows Host Deployment (No Docker)

If Docker is not available, you must install and run the services individually on your Windows machine.

### Requirements:
1. **Node.js (v18+)**: Install from the [official site](https://nodejs.org/).
2. **Python (3.11+)**: Install from the [Microsoft Store](https://apps.microsoft.com/detail/9nrwmjp3717k) or Python.org (ensure you check **"Add Python to PATH"** during setup).
3. **PostgreSQL**: Download and install [PostgreSQL for Windows](https://www.postgresql.org/download/windows/). Create a database named `aarogya` with user `postgres` and password `postgres`.
4. **Redis**: Download and install [Redis for Windows](https://github.com/tporadowski/redis/releases). Run `redis-server.exe` to start the broker on port `6379`.

### Startup Instructions:

#### 1. Setup the Database Schema
Open pgAdmin or psql and execute the DDL queries inside [schema.sql](file:///c:/Users/sandh/Downloads/Telegram%20Ai/schema.sql) to build the database tables.

#### 2. Run the Next.js Frontend
```bash
cd frontend
npm install
npm run dev
# The dashboard will launch on http://localhost:3000
```

#### 3. Run the FastAPI Backend
Ensure your `.env` variables point database and redis server connections to `localhost` (uncomment the local overrides in `.env`):
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# The backend will start on http://localhost:8000
```

#### 4. Run the Celery Worker
Make sure Redis is active. Open a new terminal session, activate the Python virtual environment, and run:
```bash
cd backend
venv\Scripts\activate
celery -A app.tasks.celery_worker.celery_app worker --loglevel=info -P threads
# Note: On Windows, use '-P threads' or '-P gevent' as Celery does not support standard fork processes on Windows.
```

#### 5. Run the Telegram Bot Daemon
Open a new terminal session, activate the virtual environment, and run:
```bash
cd telegram_bot
# The bot imports backend modules, so ensure backend dependencies are available
python bot/main.py
```
