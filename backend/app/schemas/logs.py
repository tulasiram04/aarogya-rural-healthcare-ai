from datetime import datetime
import uuid
from pydantic import BaseModel, Field

# --- Symptom Log Schemas ---
class SymptomLogBase(BaseModel):
    patient_id: uuid.UUID
    answers: dict = Field(default_factory=dict)
    input_voice_url: str | None = None
    transcript: str | None = None
    severity_score: int = Field(default=0, ge=0, le=10)

class SymptomLogCreate(SymptomLogBase):
    pass

class SymptomLogResponse(SymptomLogBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# --- Risk Alert Schemas ---
class RiskAlertBase(BaseModel):
    patient_id: uuid.UUID
    risk_level: str = "low" # low, medium, high, critical
    source: str
    alert_message: str
    status: str = "raised" # raised, acknowledged, resolved
    acknowledged_by: uuid.UUID | None = None
    resolved_at: datetime | None = None
    severity: str | None = None
    reason: str | None = None
    recommendation: str | None = None

class RiskAlertCreate(RiskAlertBase):
    pass

class RiskAlertUpdate(BaseModel):
    status: str
    acknowledged_by: uuid.UUID | None = None
    resolved_at: datetime | None = None

class RiskAlertResponse(RiskAlertBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# --- Chat History Schemas ---
class ChatHistoryBase(BaseModel):
    patient_id: uuid.UUID
    sender: str # patient | bot
    message: str
    local_language: str = "english"

class ChatHistoryCreate(ChatHistoryBase):
    pass

class ChatHistoryResponse(ChatHistoryBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
