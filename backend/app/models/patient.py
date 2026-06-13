import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.user import User

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    village: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    sub_center: Mapped[str | None] = mapped_column(String(100), nullable=True)
    blood_group: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profile_completion: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    
    assigned_hcw_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assigned_doctor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    preferred_language: Mapped[str] = mapped_column(String(50), default="english", nullable=False)
    medical_history: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    risk_score: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(50), default="low", nullable=True)
    risk_factors: Mapped[list | None] = mapped_column(JSONB, default=list, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    assigned_hcw: Mapped["User"] = relationship("User", foreign_keys=[assigned_hcw_id], back_populates="patients_as_hcw")
    assigned_doctor: Mapped["User"] = relationship("User", foreign_keys=[assigned_doctor_id], back_populates="patients_as_doctor")
    
    prescriptions: Mapped[list["Prescription"]] = relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    reminders: Mapped[list["Reminder"]] = relationship("Reminder", back_populates="patient", cascade="all, delete-orphan")
    lab_reports: Mapped[list["LabReport"]] = relationship("LabReport", back_populates="patient", cascade="all, delete-orphan")
    symptom_logs: Mapped[list["SymptomLog"]] = relationship("SymptomLog", back_populates="patient", cascade="all, delete-orphan")
    risk_alerts: Mapped[list["RiskAlert"]] = relationship("RiskAlert", back_populates="patient", cascade="all, delete-orphan")
    chat_histories: Mapped[list["ChatHistory"]] = relationship("ChatHistory", back_populates="patient", cascade="all, delete-orphan")
    activity_logs: Mapped[list["ActivityLog"]] = relationship("ActivityLog", back_populates="patient", cascade="all, delete-orphan")
