"""Repository layer — data access for parsed resume records."""

from __future__ import annotations

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from shared.logging import get_logger

from backend.modules.resume_parser.models import ParsedResumeRecord

logger = get_logger(__name__)


class ResumeRepository:
    """CRUD operations on the ``parsed_resumes`` table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: ParsedResumeRecord) -> ParsedResumeRecord:
        """Insert a new parsed resume record."""
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        logger.info(
            "Resume Parsed",
            parse_id=record.parse_id,
            filename=record.filename,
        )
        return record

    async def get_by_id(self, parse_id: str) -> ParsedResumeRecord | None:
        """Fetch a single record by parse ID."""
        result = await self._session.execute(
            select(ParsedResumeRecord).where(
                ParsedResumeRecord.parse_id == parse_id
            )
        )
        return result.scalar_one_or_none()

    async def list_records(
        self, limit: int = 20, offset: int = 0
    ) -> list[ParsedResumeRecord]:
        """List parse records ordered by most recent."""
        stmt = (
            select(ParsedResumeRecord)
            .order_by(ParsedResumeRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, parse_id: str) -> bool:
        """Delete a parse record. Returns True if a row was removed."""
        result = await self._session.execute(
            delete(ParsedResumeRecord).where(
                ParsedResumeRecord.parse_id == parse_id
            )
        )
        await self._session.commit()
        deleted = result.rowcount > 0
        if deleted:
            logger.info("Resume Record Deleted", parse_id=parse_id)
        return deleted
