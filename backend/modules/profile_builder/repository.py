"""Repository layer — data access for Candidate Profiles."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from shared.logging import get_logger

from backend.modules.profile_builder.models import CandidateProfile
from backend.modules.profile_builder.schemas import ProfileSearchFilters

logger = get_logger(__name__)


class ProfileRepository:
    """CRUD + search operations on the ``candidate_profiles`` table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Create ──────────────────────────────────────────────────────

    async def create(self, profile: CandidateProfile) -> CandidateProfile:
        """Insert a new profile row."""
        self._session.add(profile)
        await self._session.commit()
        await self._session.refresh(profile)
        logger.info(
            "Profile Created",
            candidate_id=profile.candidate_id,
            email=profile.email,
        )
        return profile

    # ── Read ────────────────────────────────────────────────────────

    async def get_by_id(self, candidate_id: str) -> CandidateProfile | None:
        """Fetch a single profile by its UUID."""
        result = await self._session.execute(
            select(CandidateProfile).where(
                CandidateProfile.candidate_id == candidate_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> CandidateProfile | None:
        """Fetch a profile by email address."""
        result = await self._session.execute(
            select(CandidateProfile).where(
                CandidateProfile.email == email.lower().strip()
            )
        )
        return result.scalar_one_or_none()

    # ── Update ──────────────────────────────────────────────────────

    async def update(self, profile: CandidateProfile) -> CandidateProfile:
        """Persist changes to an existing profile."""
        profile.updated_at = datetime.now(timezone.utc)
        self._session.add(profile)
        await self._session.commit()
        await self._session.refresh(profile)
        logger.info(
            "Profile Updated",
            candidate_id=profile.candidate_id,
        )
        return profile

    # ── Delete ──────────────────────────────────────────────────────

    async def delete(self, candidate_id: str) -> bool:
        """Hard-delete a profile by ID. Returns True if a row was removed."""
        result = await self._session.execute(
            delete(CandidateProfile).where(
                CandidateProfile.candidate_id == candidate_id
            )
        )
        await self._session.commit()
        deleted = result.rowcount > 0
        if deleted:
            logger.info("Profile Deleted", candidate_id=candidate_id)
        return deleted

    # ── Search ──────────────────────────────────────────────────────

    async def search(self, filters: ProfileSearchFilters) -> list[CandidateProfile]:
        """Search profiles with optional filters."""
        stmt = select(CandidateProfile)

        if filters.skill:
            # JSONB containment: skills array contains an element with matching name
            stmt = stmt.where(
                CandidateProfile.skills.op("@>")(
                    [{"name": filters.skill}]
                )
            )

        if filters.location:
            stmt = stmt.where(
                CandidateProfile.location.ilike(f"%{filters.location}%")
            )

        if filters.education_level:
            stmt = stmt.where(
                CandidateProfile.education.op("@>")(
                    [{"degree": filters.education_level}]
                )
            )

        if filters.status:
            stmt = stmt.where(CandidateProfile.status == filters.status)

        stmt = stmt.offset(filters.offset).limit(filters.limit)

        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())

        logger.debug("Search completed", result_count=len(rows))
        return rows
