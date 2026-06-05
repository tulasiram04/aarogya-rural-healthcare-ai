from datetime import datetime, date, time
import uuid
from pydantic import BaseModel, Field

# --- Prescription Schemas ---
class PrescriptionBase(BaseModel):
    patient_id: uuid.UUID
    raw_image_url: str
    raw_ocr_text: str | None = None
    structured_data: list = Field(default_factory=list)
    issue_date: date | None = None

class PrescriptionCreate(PrescriptionBase):
    pass

class PrescriptionResponse(PrescriptionBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# --- Reminder Schemas ---
class ReminderBase(BaseModel):
    patient_id: uuid.UUID
    prescription_id: uuid.UUID | None = None
    medicine_name: str
    dosage: str | None = None
    schedule_time: time
    frequency: str = "daily"
    is_active: bool = True
    start_date: date
    end_date: date | None = None

class ReminderCreate(ReminderBase):
    pass

class ReminderResponse(ReminderBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# --- Compliance Log Schemas ---
class ComplianceLogBase(BaseModel):
    reminder_id: uuid.UUID
    scheduled_time: datetime
    taken_time: datetime | None = None
    status: str = "pending" # pending, taken, missed, delayed
    response_voice_url: str | None = None

class ComplianceLogCreate(ComplianceLogBase):
    pass

class ComplianceLogUpdate(BaseModel):
    taken_time: datetime | None = None
    status: str
    response_voice_url: str | None = None

class ComplianceLogResponse(ComplianceLogBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# --- Lab Report Schemas ---
class LabReportBase(BaseModel):
    patient_id: uuid.UUID
    file_url: str
    report_type: str | None = None
    raw_ocr_text: str | None = None
    extracted_metrics: dict = Field(default_factory=dict)
    summary_local_lang: str | None = None

class LabReportCreate(LabReportBase):
    pass

class LabReportResponse(LabReportBase):
    id: uuid.UUID
    uploaded_at: datetime

    class Config:
        from_attributes = True
