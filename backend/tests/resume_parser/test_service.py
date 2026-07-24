"""Tests for ResumeParserService business logic."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from shared.exceptions import DatabaseException, NotFoundException, ValidationException

from backend.modules.resume_parser.schemas import ParseResult, ParseStatus
from backend.modules.resume_parser.service import ResumeParserService


class TestParseResume:
    @pytest.mark.asyncio
    async def test_parse_valid_docx(self, parser_service, mock_repository, sample_docx_bytes):
        mock_repository.create = AsyncMock(
            side_effect=lambda r: r
        )
        result = await parser_service.parse_resume(
            sample_docx_bytes, "resume.docx"
        )
        assert isinstance(result, ParseResult)
        assert result.status == ParseStatus.COMPLETED
        assert result.metadata.filename == "resume.docx"
        assert result.metadata.file_type.value == "docx"
        assert result.parsed_data.personal_info is not None

    @pytest.mark.asyncio
    async def test_rejects_unsupported_file_type(self, parser_service):
        with pytest.raises(ValidationException):
            await parser_service.parse_resume(b"some data", "resume.txt")

    @pytest.mark.asyncio
    async def test_rejects_empty_file(self, parser_service):
        with pytest.raises(ValidationException):
            await parser_service.parse_resume(b"", "resume.pdf")

    @pytest.mark.asyncio
    async def test_rejects_oversized_file(self, parser_service):
        large = b"x" * (10 * 1024 * 1024 + 1)
        with pytest.raises(ValidationException):
            await parser_service.parse_resume(large, "resume.pdf")

    @pytest.mark.asyncio
    async def test_handles_db_failure(self, parser_service, mock_repository, sample_docx_bytes):
        mock_repository.create = AsyncMock(side_effect=Exception("DB down"))
        with pytest.raises(DatabaseException):
            await parser_service.parse_resume(sample_docx_bytes, "resume.docx")

    @pytest.mark.asyncio
    async def test_stores_raw_text(self, parser_service, mock_repository, sample_docx_bytes):
        stored_record = None

        async def capture_create(record):
            nonlocal stored_record
            stored_record = record
            return record

        mock_repository.create = AsyncMock(side_effect=capture_create)
        await parser_service.parse_resume(sample_docx_bytes, "resume.docx")
        assert stored_record is not None
        assert stored_record.raw_text is not None
        assert len(stored_record.raw_text) > 0

    @pytest.mark.asyncio
    async def test_can_skip_raw_text_storage(self, parser_service, mock_repository, sample_docx_bytes):
        stored_record = None

        async def capture_create(record):
            nonlocal stored_record
            stored_record = record
            return record

        mock_repository.create = AsyncMock(side_effect=capture_create)
        await parser_service.parse_resume(
            sample_docx_bytes, "resume.docx", store_raw_text=False
        )
        assert stored_record.raw_text is None


class TestGetParseResult:
    @pytest.mark.asyncio
    async def test_returns_result(self, parser_service, mock_repository, sample_parse_result):
        record = MagicMock()
        record.parse_id = "test-001"
        record.filename = "resume.pdf"
        record.file_type = ".pdf"
        record.file_size_bytes = 1024
        record.raw_text = "some text"
        record.parsed_data = sample_parse_result.parsed_data.model_dump()
        record.status = "completed"
        record.ai_model = "gpt-4o-mini"
        record.parser_version = "1.0.0"
        record.parse_duration_ms = 150.0
        record.errors = []
        record.created_at = None

        mock_repository.get_by_id = AsyncMock(return_value=record)
        result = await parser_service.get_parse_result("test-001")
        assert result.metadata.parse_id == "test-001"

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self, parser_service, mock_repository):
        mock_repository.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundException):
            await parser_service.get_parse_result("nonexistent")


class TestDeleteParseResult:
    @pytest.mark.asyncio
    async def test_deletes(self, parser_service, mock_repository):
        mock_repository.delete = AsyncMock(return_value=True)
        await parser_service.delete_parse_result("test-001")
        mock_repository.delete.assert_awaited_once_with("test-001")

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self, parser_service, mock_repository):
        mock_repository.delete = AsyncMock(return_value=False)
        with pytest.raises(NotFoundException):
            await parser_service.delete_parse_result("nonexistent")


class TestListParseHistory:
    @pytest.mark.asyncio
    async def test_returns_results(self, parser_service, mock_repository, sample_parse_result):
        mock_repository.list_records = AsyncMock(
            return_value=[MagicMock(
                parse_id="1",
                filename="r.pdf",
                file_type=".pdf",
                file_size_bytes=1024,
                raw_text="text",
                parsed_data=sample_parse_result.parsed_data.model_dump(),
                status="completed",
                ai_model=None,
                parser_version="1.0.0",
                parse_duration_ms=100.0,
                errors=[],
                created_at=None,
            )]
        )
        results = await parser_service.list_parse_history()
        assert len(results) == 1
