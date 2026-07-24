"""
Talencia — Centralized Configuration Management.

Loads environment variables from .env via Pydantic BaseSettings.
Never hardcode secrets — always use this module.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/talencia"

    # Environment
    ENVIRONMENT: str = "development"

    # Application
    APP_NAME: str = "Talencia"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Frontend / CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # AI providers (module-specific; each provider is optional)
    AI_PROVIDER_MODE: str = "mock"
    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    JWT_SECRET: str | None = None
    MAX_UPLOAD_MB: int = 10

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance (singleton)."""
    return Settings()


settings = get_settings()
