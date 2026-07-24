"""
Single source of configuration. Per Chapter 2.14 — one .env file, never
hardcode secrets.
"""
import os
from pydantic import BaseModel


class Settings(BaseModel):
    environment: str = os.getenv("ENVIRONMENT", "development")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    ai_provider_mode: str = os.getenv("AI_PROVIDER_MODE", "mock")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")

    jwt_secret: str | None = os.getenv("JWT_SECRET")
    database_url: str | None = os.getenv("DATABASE_URL")

    max_upload_mb: int = 10


settings = Settings()
