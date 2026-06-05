import uuid
from datetime import datetime, date, time, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Date, Time, Text, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_image_url: Mapped[str] = mapped_column(Text, nullable=False)
    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_data: Mapped[list] = mapped_column(JSONB, default=list, nullable=False) # e.g., list of dicts with meds
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="prescriptions")
    reminders: Mapped[list["Reminder"]] = relationship("Reminder", back_populates="prescription", cascade="all, delete-orphan")


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    prescription_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True)
    medicine_name: Mapped[str] = mapped_column(String(150), nullable=False)
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    schedule_time: Mapped[time] = mapped_column(Time, nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), default="daily", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, default=lambda: datetime.now(timezone.utc).date(), nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="reminders")
    prescription: Mapped["Prescription"] = relationship("Prescription", back_populates="reminders")
    compliance_logs: Mapped[list["ComplianceLog"]] = relationship("ComplianceLog", back_populates="reminder", cascade="all, delete-orphan")


class ComplianceLog(Base):
    __tablename__ = "compliance_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    reminder_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reminders.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    taken_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True) # pending, taken, missed, delayed
    response_voice_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    reminder: Mapped["Reminder"] = relationship("Reminder", back_populates="compliance_logs")


class LabReport(Base):
    __tablename__ = "lab_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    report_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_metrics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False) # e.g. {"HbA1c": 8.2}
    summary_local_lang: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="lab_reports")
