"""Tests for the Profile Builder API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from shared.exceptions import (
    DuplicateException,
    NotFoundException,
    ValidationException,
)

from backend.modules.profile_builder.api import (
    router,
    get_profile_service,
    set_profile_service,
)
from backend.modules.profile_builder.models import CandidateProfile
from backend.modules.profile_builder.schemas import (
    CompletenessResult,
    ProfileMetadata,
    ProfileResponse,
)


def _make_response(**overrides) -> ProfileResponse:
    from backend.modules.profile_builder.schemas import (
        LinkItem,
        PersonalInfo,
    )

    defaults = dict(
        candidate_id="test-id",
        personal_info=PersonalInfo(
            first_name="Jane",
            last_name="Doe",
            email="jane@test.com",
        ),
        summary="Summary",
        education=[],
        experience=[],
        skills=[],
        projects=[],
        certifications=[],
        links=[
            LinkItem(label="LinkedIn", url="https://linkedin.com/in/jane"),
            LinkItem(label="GitHub", url="https://github.com/jane"),
        ],
        metadata=ProfileMetadata(
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        completeness=CompletenessResult(score=75.0, status="good"),
        status="good",
    )
    defaults.update(overrides)
    return ProfileResponse(**defaults)


@pytest.fixture
def mock_service():
    svc = MagicMock()
    svc.create_profile = AsyncMock()
    svc.get_profile = AsyncMock()
    svc.update_profile = AsyncMock()
    svc.delete_profile = AsyncMock()
    svc.search_profiles = AsyncMock()
    return svc


@pytest.fixture
def client(mock_service):
    app = FastAPI()
    app.include_router(router)
    set_profile_service(mock_service)
    return TestClient(app, raise_server_exceptions=False)


class TestCreateProfileEndpoint:
    def test_creates_profile(self, client, mock_service):
        mock_service.create_profile.return_value = _make_response(candidate_id="new-id")

        response = client.post(
            "/profile",
            json={
                "personal_info": {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email": "jane@test.com",
                },
                "skills": [{"name": "Python"}],
                "links": [
                    {"label": "LinkedIn", "url": "https://linkedin.com/in/jane"},
                    {"label": "GitHub", "url": "https://github.com/jane"},
                ],
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["candidate_id"] == "new-id"

    def test_validation_error(self, client, mock_service):
        """Validation error from business logic (not Pydantic)."""
        mock_service.create_profile.side_effect = ValidationException(
            message="Validation failed",
            errors={"required": ["email is required"]},
        )
        response = client.post(
            "/profile",
            json={
                "personal_info": {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email": "jane@test.com",
                },
                "skills": [{"name": "Python"}],
            },
        )
        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert body["message"] == "Validation failed"

    def test_duplicate_email(self, client, mock_service):
        mock_service.create_profile.side_effect = DuplicateException(
            message="Email already exists"
        )
        response = client.post(
            "/profile",
            json={
                "personal_info": {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email": "jane@test.com",
                },
                "skills": [{"name": "Python"}],
            },
        )
        assert response.status_code == 409


class TestGetProfileEndpoint:
    def test_retrieves_profile(self, client, mock_service):
        mock_service.get_profile.return_value = _make_response()
        response = client.get("/profile/test-id")
        assert response.status_code == 200
        assert response.json()["data"]["candidate_id"] == "test-id"

    def test_not_found(self, client, mock_service):
        mock_service.get_profile.side_effect = NotFoundException(
            "CandidateProfile", "missing"
        )
        response = client.get("/profile/missing")
        assert response.status_code == 404


class TestUpdateProfileEndpoint:
    def test_updates_profile(self, client, mock_service):
        mock_service.update_profile.return_value = _make_response(
            summary="Updated"
        )
        response = client.put(
            "/profile/test-id",
            json={"summary": "Updated"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["summary"] == "Updated"

    def test_not_found(self, client, mock_service):
        mock_service.update_profile.side_effect = NotFoundException(
            "CandidateProfile", "missing"
        )
        response = client.put(
            "/profile/missing",
            json={"summary": "X"},
        )
        assert response.status_code == 404


class TestDeleteProfileEndpoint:
    def test_deletes_profile(self, client, mock_service):
        mock_service.delete_profile.return_value = None
        response = client.delete("/profile/test-id")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_not_found(self, client, mock_service):
        mock_service.delete_profile.side_effect = NotFoundException(
            "CandidateProfile", "missing"
        )
        response = client.delete("/profile/missing")
        assert response.status_code == 404


class TestSearchProfilesEndpoint:
    def test_search_returns_results(self, client, mock_service):
        mock_service.search_profiles.return_value = [
            _make_response(candidate_id="1"),
            _make_response(candidate_id="2"),
        ]
        response = client.get("/profile/search?skill=Python")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 2

    def test_search_empty_results(self, client, mock_service):
        mock_service.search_profiles.return_value = []
        response = client.get("/profile/search")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_search_with_location_filter(self, client, mock_service):
        mock_service.search_profiles.return_value = [_make_response()]
        response = client.get("/profile/search?location=NYC")
        assert response.status_code == 200
