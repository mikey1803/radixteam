"""Tests for the ProfileService business logic layer."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from shared.exceptions import (
    DatabaseException,
    DuplicateException,
    NotFoundException,
    ValidationException,
)

from backend.modules.profile_builder.models import CandidateProfile
from backend.modules.profile_builder.schemas import (
    LinkItem,
    PersonalInfo,
    ProfileCreate,
    ProfileSearchFilters,
    ProfileUpdate,
    SkillItem,
)
from backend.modules.profile_builder.service import ProfileService


def _make_model(**overrides) -> CandidateProfile:
    now = datetime.now(timezone.utc)
    defaults = dict(
        candidate_id="test-id",
        first_name="Jane",
        last_name="Doe",
        email="jane@test.com",
        phone="+15551234567",
        location="NYC",
        headline="Engineer",
        summary="Summary",
        education=[],
        experience=[],
        skills=[{"name": "Python"}],
        projects=[],
        certifications=[],
        links=[
            {"label": "LinkedIn", "url": "https://linkedin.com/in/jane"},
            {"label": "GitHub", "url": "https://github.com/jane"},
        ],
        completeness_score=75.0,
        status="good",
        parser_version="1.0",
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return CandidateProfile(**defaults)


class TestCreateProfile:
    @pytest.mark.asyncio
    async def test_creates_valid_profile(self, profile_service, mock_repository):
        mock_repository.get_by_email.return_value = None
        saved_model = _make_model(candidate_id="new-id")
        mock_repository.create.return_value = saved_model

        payload = ProfileCreate(
            personal_info=PersonalInfo(
                first_name="Jane",
                last_name="Doe",
                email="jane@test.com",
            ),
            skills=[SkillItem(name="Python")],
            links=[
                LinkItem(label="LinkedIn", url="https://linkedin.com/in/jane"),
                LinkItem(label="GitHub", url="https://github.com/jane"),
            ],
        )
        result = await profile_service.create_profile(payload)
        assert result.candidate_id == "new-id"
        mock_repository.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rejects_duplicate_email(self, profile_service, mock_repository):
        mock_repository.get_by_email.return_value = _make_model()

        payload = ProfileCreate(
            personal_info=PersonalInfo(
                first_name="Jane",
                last_name="Doe",
                email="jane@test.com",
            ),
            skills=[SkillItem(name="Python")],
        )
        with pytest.raises(DuplicateException):
            await profile_service.create_profile(payload)

    @pytest.mark.asyncio
    async def test_rejects_invalid_payload(self, profile_service, mock_repository):
        """Test business-level validation (empty skills list)."""
        payload = ProfileCreate(
            personal_info=PersonalInfo(
                first_name="Jane",
                last_name="Doe",
                email="jane@test.com",
            ),
            skills=[],
        )
        with pytest.raises(ValidationException):
            await profile_service.create_profile(payload)

    @pytest.mark.asyncio
    async def test_handles_db_failure(self, profile_service, mock_repository):
        mock_repository.get_by_email.return_value = None
        mock_repository.create.side_effect = Exception("DB down")

        payload = ProfileCreate(
            personal_info=PersonalInfo(
                first_name="Jane",
                last_name="Doe",
                email="jane@test.com",
            ),
            skills=[SkillItem(name="Python")],
        )
        with pytest.raises(DatabaseException):
            await profile_service.create_profile(payload)


class TestGetProfile:
    @pytest.mark.asyncio
    async def test_returns_profile(self, profile_service, mock_repository):
        mock_repository.get_by_id.return_value = _make_model()
        result = await profile_service.get_profile("test-id")
        assert result.candidate_id == "test-id"

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self, profile_service, mock_repository):
        mock_repository.get_by_id.return_value = None
        with pytest.raises(NotFoundException):
            await profile_service.get_profile("nonexistent")


class TestUpdateProfile:
    @pytest.mark.asyncio
    async def test_updates_profile(self, profile_service, mock_repository):
        model = _make_model()
        mock_repository.get_by_id.return_value = model
        mock_repository.update.return_value = model

        update = ProfileUpdate(summary="Updated summary")
        result = await profile_service.update_profile("test-id", update)
        assert result.summary == "Updated summary"

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self, profile_service, mock_repository):
        mock_repository.get_by_id.return_value = None
        with pytest.raises(NotFoundException):
            await profile_service.update_profile("nonexistent", ProfileUpdate())

    @pytest.mark.asyncio
    async def test_rejects_invalid_update(self, profile_service, mock_repository):
        mock_repository.get_by_id.return_value = _make_model()
        update = ProfileUpdate(skills=[])
        with pytest.raises(ValidationException):
            await profile_service.update_profile("test-id", update)


class TestDeleteProfile:
    @pytest.mark.asyncio
    async def test_deletes_profile(self, profile_service, mock_repository):
        mock_repository.get_by_id.return_value = _make_model()
        mock_repository.delete.return_value = True
        await profile_service.delete_profile("test-id")
        mock_repository.delete.assert_awaited_once_with("test-id")

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self, profile_service, mock_repository):
        mock_repository.get_by_id.return_value = None
        with pytest.raises(NotFoundException):
            await profile_service.delete_profile("nonexistent")

    @pytest.mark.asyncio
    async def test_handles_db_failure_on_delete(self, profile_service, mock_repository):
        mock_repository.get_by_id.return_value = _make_model()
        mock_repository.delete.side_effect = Exception("DB error")
        with pytest.raises(DatabaseException):
            await profile_service.delete_profile("test-id")


class TestSearchProfiles:
    @pytest.mark.asyncio
    async def test_returns_results(self, profile_service, mock_repository):
        mock_repository.search.return_value = [_make_model(), _make_model()]
        filters = ProfileSearchFilters(skill="Python")
        results = await profile_service.search_profiles(filters)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_handles_db_failure(self, profile_service, mock_repository):
        mock_repository.search.side_effect = Exception("DB error")
        with pytest.raises(DatabaseException):
            await profile_service.search_profiles(ProfileSearchFilters())

    @pytest.mark.asyncio
    async def test_empty_results(self, profile_service, mock_repository):
        mock_repository.search.return_value = []
        results = await profile_service.search_profiles(ProfileSearchFilters())
        assert results == []
