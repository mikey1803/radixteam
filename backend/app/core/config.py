"""
Talencia — Centralized Configuration Management.

Loads environment variables from .env via Pydantic BaseSettings.
Never hardcode secrets — always use this module.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance (singleton)."""
    return Settings()
