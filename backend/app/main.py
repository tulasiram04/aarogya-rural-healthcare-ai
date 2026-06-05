import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.core.config import settings
from app.api import auth, patients, prescriptions, reports, reminders, alerts, dashboard, activity, assistant
from app.core.migrate import run_migrations

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("aarogya.main")

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic AI Rural Healthcare Platform API gateway.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS policies
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directories exist and mount StaticFiles
os.makedirs("/workspace/uploads/prescriptions", exist_ok=True)
os.makedirs("/workspace/uploads/reports", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="/workspace/uploads"), name="uploads")

# Register API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(patients.router, prefix=settings.API_V1_STR)
app.include_router(prescriptions.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(reminders.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(activity.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["system"])
def health_check():
    """System health check endpoint for monitoring servers."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

run_migrations()
logger.info("FastAPI AAROGYA engine successfully compiled and loaded.")
