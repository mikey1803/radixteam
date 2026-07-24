"""
Application configuration using python-dotenv + os.getenv().
All values can be overridden via environment variables or a .env file.
"""

import os
from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv

# Load .env file (if it exists) into environment
load_dotenv()


class Settings:
    """Central configuration for the application — reads from environment."""

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = os.getenv("APP_NAME", "RadixTeam API")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # ── Server ───────────────────────────────────────────────────────────
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
        ).split(",")
    ]

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./radixteam.db"
    )

    # ── JWT / Auth ───────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    # ── AI Provider ──────────────────────────────────────────────────────
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # ── Logging ──────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — call this instead of Settings() directly."""
    return Settings()
