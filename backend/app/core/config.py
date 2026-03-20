"""
Application configuration management using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Enterprise Health Report API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://health_user:health_password@postgres-kimi:5432/health_db_kimi"

    # Redis
    REDIS_URL: str = "redis://redis-kimi:6379/0"

    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3005", "http://127.0.0.1:3005"]

    # LLM API (Phase 4)
    LLM_API_BASE_URL: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL_NAME: str = "gpt-4"

    # Encryption
    ENCRYPTION_KEY: str = "your-encryption-key-change-in-production"  # Fernet key

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
