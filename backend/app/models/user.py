import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # 'doctor', 'hcw', 'admin', 'system'
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

    # Relationships
    patients_as_hcw: Mapped[list["Patient"]] = relationship(
        "Patient", 
        foreign_keys="[Patient.assigned_hcw_id]", 
        back_populates="assigned_hcw"
    )
    patients_as_doctor: Mapped[list["Patient"]] = relationship(
        "Patient", 
        foreign_keys="[Patient.assigned_doctor_id]", 
        back_populates="assigned_doctor"
    )
    alerts_acknowledged: Mapped[list["RiskAlert"]] = relationship(
        "RiskAlert",
        back_populates="acknowledged_by_user"
    )
