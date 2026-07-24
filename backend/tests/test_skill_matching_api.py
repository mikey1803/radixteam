"""
Skill Matching — Milestone 12 Integration Tests (api.py + main.py).

Hits the real, fully-wired FastAPI app through TestClient — router
registration (app/api/router.py), global exception handlers (app/main.py),
dependency injection (app/api/dependencies.py), and the shared
APIResponse envelope all exercised together, exactly as a real client
would see them. No live AI network calls anywhere in this file: the
default (no API key configured in this environment) exercises the
template-fallback path for free, and the AI path is exercised by
overriding the get_ai_provider dependency with a fake.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_ai_provider
from app.main import app
from modules.skill_matching.reasoning import AIExplanationResponse, ExplanationPoint

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "skill_matching"
client = TestClient(app)


def _load(name: str) -> dict:
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class _FakeProvider:
    def __init__(self, response):
        self._response = response

    def complete_structured(self, system_prompt, user_prompt, response_model, *, temperature=0.2, timeout_seconds=10.0):
        return self._response


# ─── Health check ──────────────────────────────────────────────────────────

def test_health_check_returns_running_status():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True


# ─── POST /api/v1/skill-match ──────────────────────────────────────────────

class TestMatchEndpoint:
    def test_valid_request_returns_full_response_shape(self):
        payload = {"job": _load("job_fixture.json"), "candidate": _load("candidate_fixture.json")}
        response = client.post("/api/v1/skill-match", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        data = body["data"]

        assert data["candidate_id"] == "cand-001"
        assert data["job_id"] == "job-101"
        assert data["schema_version"] == "1.0.0"
        assert isinstance(data["overall_score"], float)
        assert isinstance(data["overall_confidence"], float)
        assert isinstance(data["matched_skills"], list)
        assert isinstance(data["gaps"], list)
        assert data["recommendation"]["tier"] in {
            "strong_match", "good_match", "potential_match", "needs_upskilling", "low_match",
        }
        assert data["explanation"]
        assert data["explanation_source"] in {"ai", "template"}
        assert data["insights"] is not None
        assert "interview_questions" in data["insights"]

    def test_empty_job_returns_400_through_global_exception_handler(self):
        payload = {"job": _load("job_empty_fixture.json"), "candidate": _load("candidate_fixture.json")}
        response = client.post("/api/v1/skill-match", json=payload)

        assert response.status_code == 400
        body = response.json()
        assert body["success"] is False
        assert body["message"]

    def test_malformed_request_body_returns_422(self):
        # missing required "candidate" field entirely -- FastAPI/pydantic
        # request validation, not our ValidationError -- proves the two
        # validation layers don't collide.
        response = client.post("/api/v1/skill-match", json={"job": {}})
        assert response.status_code == 422

    def test_response_matches_schema_exactly_via_matched_skill_shape(self):
        payload = {"job": _load("job_fixture.json"), "candidate": _load("candidate_fixture.json")}
        response = client.post("/api/v1/skill-match", json=payload)
        matched = response.json()["data"]["matched_skills"]

        python_entry = next(m for m in matched if m["skill"] == "Python")
        assert python_entry["match_type"] == "exact"
        assert 0 <= python_entry["confidence"] <= 1
        assert isinstance(python_entry["evidence"], list)

    def test_uses_ai_explanation_when_provider_is_available(self):
        ai_response = AIExplanationResponse(
            overall_summary="Overall strong alignment.",
            points=[ExplanationPoint(statement="Python is directly matched.", cites_skill="Python")],
        )
        app.dependency_overrides[get_ai_provider] = lambda: _FakeProvider(ai_response)
        try:
            payload = {"job": _load("job_fixture.json"), "candidate": _load("candidate_fixture.json")}
            response = client.post("/api/v1/skill-match", json=payload)
            data = response.json()["data"]
            assert data["explanation_source"] == "ai"
            assert "Python is directly matched" in data["explanation"]
        finally:
            app.dependency_overrides.pop(get_ai_provider, None)

    def test_falls_back_to_template_when_no_ai_provider_configured(self):
        # No override here -- in this environment, no API key is
        # configured, so get_ai_provider() naturally resolves to None.
        payload = {"job": _load("job_fixture.json"), "candidate": _load("candidate_fixture.json")}
        response = client.post("/api/v1/skill-match", json=payload)
        assert response.json()["data"]["explanation_source"] == "template"


# ─── POST /api/v1/skill-match/what-if ─────────────────────────────────────

class TestWhatIfEndpoint:
    def test_valid_request_returns_expected_shape(self):
        payload = {
            "job": _load("job_fixture.json"),
            "candidate": _load("candidate_sparse_fixture.json"),
            "hypothetical_skill": "Python",
        }
        response = client.post("/api/v1/skill-match/what-if", json=payload)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["hypothetical_skill"] == "Python"
        assert data["hypothetical_skill_recognized"] is True
        assert data["score_delta"] > 0

    def test_empty_job_returns_400(self):
        payload = {
            "job": _load("job_empty_fixture.json"),
            "candidate": _load("candidate_fixture.json"),
            "hypothetical_skill": "Python",
        }
        response = client.post("/api/v1/skill-match/what-if", json=payload)
        assert response.status_code == 400
