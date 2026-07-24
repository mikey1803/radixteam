"""Backend API dependencies — FastAPI dependency injection wiring."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.profile_builder.repository import ProfileRepository
from backend.modules.profile_builder.service import ProfileService


async def get_profile_service(session: AsyncSession) -> ProfileService:
    """Build a ProfileService wired to the current DB session."""
    repo = ProfileRepository(session)
    return ProfileService(repo)
