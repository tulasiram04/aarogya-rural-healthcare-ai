from datetime import datetime
import uuid
from pydantic import BaseModel, Field

class PatientBase(BaseModel):
    telegram_id: int | None = None
    phone: str | None = None
    full_name: str
    age: int | None = None
    gender: str | None = None
    village: str | None = None
    sub_center: str | None = None
    assigned_hcw_id: uuid.UUID | None = None
    assigned_doctor_id: uuid.UUID | None = None
    preferred_language: str = "english"
    medical_history: dict = Field(default_factory=dict)
    risk_score: int | None = 0
    risk_level: str | None = "low"
    risk_factors: list | None = []

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    phone: str | None = None
    full_name: str | None = None
    age: int | None = None
    gender: str | None = None
    village: str | None = None
    sub_center: str | None = None
    assigned_hcw_id: uuid.UUID | None = None
    assigned_doctor_id: uuid.UUID | None = None
    preferred_language: str | None = None
    medical_history: dict | None = None
    is_active: bool | None = None
    risk_score: int | None = None
    risk_level: str | None = None
    risk_factors: list | None = None

class PatientResponse(PatientBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
