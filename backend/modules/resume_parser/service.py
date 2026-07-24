"""Service layer — orchestration for the Resume Parser module."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from shared.exceptions import DatabaseException, ValidationException
from shared.logging import get_logger

from backend.modules.resume_parser.extractor import (
    PARSER_VERSION,
    extract_structured_data,
)
from backend.modules.resume_parser.models import ParsedResumeRecord
from backend.modules.resume_parser.parsers import extract_text, validate_file
from backend.modules.resume_parser.repository import ResumeRepository
from backend.modules.resume_parser.schemas import (
    FileType,
    ParseMetadata,
    ParseResult,
    ParseStatus,
    ParsedResume,
)

logger = get_logger(__name__)


class ResumeParserService:
    """Orchestrates file parsing, text extraction, and LLM structuring."""

    def __init__(self, repository: ResumeRepository) -> None:
        self._repo = repository

    async def parse_resume(
        self,
        file_bytes: bytes,
        filename: str,
        ai_model: str | None = None,
        store_raw_text: bool = True,
    ) -> ParseResult:
        """Full pipeline: validate → extract text → LLM structure → store.

        Returns a ParseResult containing structured data and metadata.
        """
        start = time.monotonic()

        # ── Validate ─────────────────────────────────────────────
        try:
            ext = validate_file(filename, len(file_bytes))
        except ValueError as exc:
            raise ValidationException(
                message=str(exc),
                errors={"filename": filename},
            ) from exc

        file_type = FileType(ext.lstrip("."))

        # ── Extract raw text ─────────────────────────────────────
        try:
            raw_text = extract_text(file_bytes, filename)
        except ValueError as exc:
            raise ValidationException(
                message=f"Text extraction failed: {exc}",
                errors={"filename": filename},
            ) from exc

        # ── LLM structured extraction ────────────────────────────
        try:
            structured = await extract_structured_data(raw_text, ai_model)
        except Exception as exc:
            logger.error("Structured extraction failed", error=str(exc))
            raise ValidationException(
                message=f"AI extraction failed: {exc}",
                errors={"filename": filename},
            ) from exc

        duration_ms = (time.monotonic() - start) * 1000

        # ── Build result ─────────────────────────────────────────
        parsed_resume = ParsedResume(**structured)

        metadata = ParseMetadata(
            filename=filename,
            file_type=file_type,
            file_size_bytes=len(file_bytes),
            raw_text_length=len(raw_text),
            ai_model=ai_model,
            parser_version=PARSER_VERSION,
            parse_duration_ms=round(duration_ms, 2),
            created_at=datetime.now(timezone.utc),
        )

        # ── Store in database ────────────────────────────────────
        parse_id = str(uuid.uuid4())
        metadata.parse_id = parse_id

        try:
            record = ParsedResumeRecord(
                parse_id=parse_id,
                filename=filename,
                file_type=ext,
                file_size_bytes=len(file_bytes),
                raw_text=raw_text if store_raw_text else None,
                parsed_data=structured,
                status=ParseStatus.COMPLETED.value,
                ai_model=ai_model,
                parser_version=PARSER_VERSION,
                parse_duration_ms=round(duration_ms, 2),
                errors=[],
                created_at=datetime.now(timezone.utc),
            )
            await self._repo.create(record)
        except Exception as exc:
            logger.error("Failed to store parse result", error=str(exc))
            raise DatabaseException("Failed to store parse result") from exc

        logger.info(
            "Resume Parse Completed",
            parse_id=parse_id,
            filename=filename,
            duration_ms=round(duration_ms, 2),
        )

        return ParseResult(
            parsed_data=parsed_resume,
            metadata=metadata,
            status=ParseStatus.COMPLETED,
        )

    async def get_parse_result(self, parse_id: str) -> ParseResult:
        """Retrieve a previous parse result by ID."""
        record = await self._repo.get_by_id(parse_id)
        if record is None:
            from shared.exceptions import NotFoundException

            raise NotFoundException("ParsedResumeRecord", parse_id)

        return ParseResult(
            parsed_data=ParsedResume(**record.parsed_data),
            metadata=ParseMetadata(
                parse_id=record.parse_id,
                filename=record.filename,
                file_type=FileType(record.file_type.lstrip(".")),
                file_size_bytes=record.file_size_bytes,
                raw_text_length=len(record.raw_text) if record.raw_text else 0,
                ai_model=record.ai_model,
                parser_version=record.parser_version,
                parse_duration_ms=record.parse_duration_ms,
                created_at=record.created_at,
            ),
            status=ParseStatus(record.status),
            errors=record.errors or [],
        )

    async def list_parse_history(
        self, limit: int = 20, offset: int = 0
    ) -> list[ParseResult]:
        """List recent parse results."""
        records = await self._repo.list_records(limit=limit, offset=offset)
        return [
            ParseResult(
                parsed_data=ParsedResume(**r.parsed_data),
                metadata=ParseMetadata(
                    parse_id=r.parse_id,
                    filename=r.filename,
                    file_type=FileType(r.file_type.lstrip(".")),
                    file_size_bytes=r.file_size_bytes,
                    ai_model=r.ai_model,
                    parser_version=r.parser_version,
                    parse_duration_ms=r.parse_duration_ms,
                    created_at=r.created_at,
                ),
                status=ParseStatus(r.status),
                errors=r.errors or [],
            )
            for r in records
        ]

    async def delete_parse_result(self, parse_id: str) -> None:
        """Delete a parse record."""
        deleted = await self._repo.delete(parse_id)
        if not deleted:
            from shared.exceptions import NotFoundException

            raise NotFoundException("ParsedResumeRecord", parse_id)
