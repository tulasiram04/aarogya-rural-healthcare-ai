from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# Create engine with pools sized appropriately for a clinical scale system
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator:
    """
    Dependency function to yield database session to FastAPI request lifecycles.
    Ensures rollback on exceptions and automatic release of connections back to pool.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
