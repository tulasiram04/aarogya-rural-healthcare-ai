from datetime import datetime
import uuid
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    phone: str = Field(..., description="Mobile number of the medical worker")
    full_name: str = Field(..., description="Full name of the medical worker")
    email: EmailStr | None = None
    role: str = Field(..., description="Role: doctor | hcw | admin")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Cryptographic access password")

class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    phone: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str | None = None
