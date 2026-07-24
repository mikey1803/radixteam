"""Tests for the ProfileRepository data-access layer."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.modules.profile_builder.models import CandidateProfile
from backend.modules.profile_builder.repository import ProfileRepository
from backend.modules.profile_builder.schemas import ProfileSearchFilters


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    return ProfileRepository(session=mock_session)


def _make_model(**overrides) -> CandidateProfile:
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
        links=[],
        completeness_score=75.0,
        status="good",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return CandidateProfile(**defaults)


class TestRepositoryCreate:
    @pytest.mark.asyncio
    async def test_create_adds_and_commits(self, repository, mock_session):
        model = _make_model()
        result = await repository.create(model)
        mock_session.add.assert_called_once_with(model)
        mock_session.commit.assert_awaited_once()
        assert result is model

    @pytest.mark.asyncio
    async def test_create_refreshes_model(self, repository, mock_session):
        model = _make_model()
        await repository.create(model)
        mock_session.refresh.assert_awaited_once_with(model)


class TestRepositoryGetById:
    @pytest.mark.asyncio
    async def test_returns_model_when_found(self, repository, mock_session):
        model = _make_model()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_id("test-id")
        assert result is model

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, repository, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_id("nonexistent")
        assert result is None


class TestRepositoryGetByEmail:
    @pytest.mark.asyncio
    async def test_returns_model_when_found(self, repository, mock_session):
        model = _make_model()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_email("jane@test.com")
        assert result is model


class TestRepositoryUpdate:
    @pytest.mark.asyncio
    async def test_updates_timestamp(self, repository, mock_session):
        model = _make_model()
        old_time = model.updated_at
        result = await repository.update(model)
        assert result.updated_at >= old_time
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_adds_and_commits(self, repository, mock_session):
        model = _make_model()
        await repository.update(model)
        mock_session.add.assert_called_once_with(model)


class TestRepositoryDelete:
    @pytest.mark.asyncio
    async def test_returns_true_when_deleted(self, repository, mock_session):
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await repository.delete("test-id")
        assert result is True
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self, repository, mock_session):
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        result = await repository.delete("nonexistent")
        assert result is False


class TestRepositorySearch:
    @pytest.mark.asyncio
    async def test_search_returns_results(self, repository, mock_session):
        models = [_make_model(candidate_id="1"), _make_model(candidate_id="2")]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = models
        mock_session.execute.return_value = mock_result

        filters = ProfileSearchFilters(skill="Python")
        result = await repository.search(filters)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_search_empty_filters(self, repository, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        filters = ProfileSearchFilters()
        result = await repository.search(filters)
        assert result == []
