import os
from typing import List
from pydantic import AnyHttpUrl, EmailStr, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AAROGYA: The Village Doctor Agent"
    API_V1_STR: str = "/api/v1"
    
    # Security & Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "SUPER_SECRET_AES_KEY_FOR_JWT_SIGNING_MINIMUM_256_BITS")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days for rural worker convenience
    ALGORITHM: str = "HS256"

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Databases
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "aarogya")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    DATABASE_URL: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, values) -> str:
        if isinstance(v, str):
            return v
        data = values.data
        return f"postgresql://{data.get('POSTGRES_USER')}:{data.get('POSTGRES_PASSWORD')}@{data.get('POSTGRES_SERVER')}:{data.get('POSTGRES_PORT')}/{data.get('POSTGRES_DB')}"

    # Cache & Queues
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Third Party Integrations
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "PLACEHOLDER_TOKEN")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "PLACEHOLDER_GEMINI_KEY")

    # File Storage (MinIO / S3)
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
    AWS_S3_ENDPOINT_URL: str = os.getenv("AWS_S3_ENDPOINT_URL", "http://localhost:9000")
    S3_BUCKET_NAME: str = "aarogya-media"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
