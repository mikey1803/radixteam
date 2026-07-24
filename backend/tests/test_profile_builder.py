"""
Profile Builder — Unit Tests.

Tests CRUD operations, validation, duplicate handling, completeness
calculation, normalization, and search functionality.

Uses SQLite in-memory database for test isolation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app


# ─── Test Database Setup (SQLite in-memory) ─────────────────────────────

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_talencia.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


def override_get_db():
    """Override the database dependency with test database."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ─── Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def _valid_profile_data() -> dict:
    """Return a valid profile creation payload."""
    return {
        "name": "Sammy Kumar",
        "email": "sammy@example.com",
        "phone": "+91 9876543210",
        "location": "Bangalore",
        "summary": "Experienced backend developer.",
        "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        "education": [
            {
                "institution": "VIT University",
                "degree": "B.Tech",
                "field_of_study": "Computer Science",
                "start_date": "2020",
                "end_date": "2024",
                "gpa": "8.5",
            }
        ],
        "experience": [
            {
                "company": "TechCorp",
                "title": "Backend Developer",
                "location": "Bangalore",
                "start_date": "2024-01",
                "end_date": None,
                "description": "Built REST APIs with FastAPI and PostgreSQL",
                "technologies": ["Python", "FastAPI", "PostgreSQL"],
            }
        ],
        "projects": [
            {
                "name": "DeploySense",
                "description": "AI-powered deployment monitoring tool",
                "technologies": ["Python", "Docker", "Kubernetes"],
                "url": "https://github.com/sammy/deploysense",
            }
        ],
        "certifications": [
            {
                "name": "AWS Cloud Practitioner",
                "issuer": "Amazon",
                "date": "2024-06",
                "url": "https://aws.amazon.com/cert/123",
            }
        ],
        "links": {
            "linkedin": "https://linkedin.com/in/sammy",
            "github": "https://github.com/sammy",
            "portfolio": "https://sammy.dev",
        },
        "metadata": {
            "resume_version": "1.0",
            "parser_version": "2.0",
            "ai_model": "gemini-pro",
        },
    }


# ─── Test: Create Profile ───────────────────────────────────────────────


class TestCreateProfile:
    """Tests for POST /profile."""

    def test_create_profile_success(self):
        """Valid resume JSON should create a profile successfully."""
        response = client.post("/profile", json=_valid_profile_data())
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Profile created successfully"
        assert data["data"]["name"] == "Sammy Kumar"
        assert data["data"]["email"] == "sammy@example.com"
        assert data["data"]["id"] is not None
        assert data["data"]["completeness_score"] > 0
        assert data["data"]["profile_status"] in [
            "Incomplete", "Average", "Good", "Excellent"
        ]

    def test_create_profile_missing_name(self):
        """Missing name should return 400."""
        payload = _valid_profile_data()
        payload["name"] = ""
        response = client.post("/profile", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "name" in str(data["errors"]).lower()

    def test_create_profile_missing_email(self):
        """Missing email should return 400."""
        payload = _valid_profile_data()
        payload["email"] = ""
        response = client.post("/profile", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "email" in str(data["errors"]).lower()

    def test_create_profile_missing_skills(self):
        """No skills should return 400."""
        payload = _valid_profile_data()
        payload["skills"] = []
        response = client.post("/profile", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "skill" in str(data["errors"]).lower()

    def test_create_profile_duplicate_email(self):
        """Duplicate email should return 409."""
        payload = _valid_profile_data()
        response1 = client.post("/profile", json=payload)
        assert response1.status_code == 201

        response2 = client.post("/profile", json=payload)
        assert response2.status_code == 409
        data = response2.json()
        assert data["success"] is False
        assert "duplicate" in data["message"].lower() or "already exists" in data["message"].lower()

    def test_create_profile_invalid_email(self):
        """Invalid email format should return 400."""
        payload = _valid_profile_data()
        payload["email"] = "not-an-email"
        response = client.post("/profile", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False


# ─── Test: Get Profile ───────────────────────────────────────────────────


class TestGetProfile:
    """Tests for GET /profile/{candidate_id}."""

    def test_get_profile_success(self):
        """Created profile should be retrievable."""
        create_resp = client.post("/profile", json=_valid_profile_data())
        assert create_resp.status_code == 201
        profile_id = create_resp.json()["data"]["id"]

        get_resp = client.get(f"/profile/{profile_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["success"] is True
        assert data["data"]["id"] == profile_id
        assert data["data"]["name"] == "Sammy Kumar"

    def test_get_profile_not_found(self):
        """Non-existent ID should return 404."""
        fake_id = "00000000-0000-4000-a000-000000000000"
        response = client.get(f"/profile/{fake_id}")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_get_profile_invalid_uuid(self):
        """Invalid UUID format should return 400."""
        response = client.get("/profile/not-a-uuid")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False


# ─── Test: Update Profile ───────────────────────────────────────────────


class TestUpdateProfile:
    """Tests for PUT /profile/{candidate_id}."""

    def test_update_profile_success(self):
        """Updating skills should succeed and recalculate completeness."""
        create_resp = client.post("/profile", json=_valid_profile_data())
        profile_id = create_resp.json()["data"]["id"]

        update_resp = client.put(
            f"/profile/{profile_id}",
            json={"skills": ["Python", "React", "TypeScript", "Node.js"]},
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["success"] is True
        assert "React" in str(data["data"]["skills"])

    def test_update_profile_not_found(self):
        """Updating non-existent profile should return 404."""
        fake_id = "00000000-0000-4000-a000-000000000000"
        response = client.put(
            f"/profile/{fake_id}",
            json={"name": "New Name"},
        )
        assert response.status_code == 404


# ─── Test: Delete Profile ───────────────────────────────────────────────


class TestDeleteProfile:
    """Tests for DELETE /profile/{candidate_id}."""

    def test_delete_profile_success(self):
        """Deleted profile should not be retrievable."""
        create_resp = client.post("/profile", json=_valid_profile_data())
        profile_id = create_resp.json()["data"]["id"]

        delete_resp = client.delete(f"/profile/{profile_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["success"] is True

        # Should be gone now
        get_resp = client.get(f"/profile/{profile_id}")
        assert get_resp.status_code == 404

    def test_delete_profile_not_found(self):
        """Deleting non-existent profile should return 404."""
        fake_id = "00000000-0000-4000-a000-000000000000"
        response = client.delete(f"/profile/{fake_id}")
        assert response.status_code == 404


# ─── Test: Search Profiles ──────────────────────────────────────────────


class TestSearchProfiles:
    """Tests for GET /profile/search."""

    def test_search_by_skill(self):
        """Search by skill should return matching profiles."""
        client.post("/profile", json=_valid_profile_data())
        response = client.get("/profile/search?skill=Python")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    def test_search_by_location(self):
        """Search by location should return matching profiles."""
        client.post("/profile", json=_valid_profile_data())
        # Location "Bangalore" is normalized to "Bengaluru"
        response = client.get("/profile/search?location=Bengaluru")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    def test_search_no_results(self):
        """Search with non-matching filter should return empty list."""
        response = client.get("/profile/search?skill=COBOL")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0


# ─── Test: Duplicate Resolution ─────────────────────────────────────────


class TestDuplicateResolution:
    """Tests for skill and project deduplication."""

    def test_duplicate_skills_resolved(self):
        """[Python, python, PYTHON] should become [Python]."""
        payload = _valid_profile_data()
        payload["skills"] = ["Python", "python", "PYTHON", "FastAPI", "fastapi"]
        response = client.post("/profile", json=payload)
        assert response.status_code == 201
        skills = response.json()["data"]["skills"]
        # Should be deduplicated (case-insensitive)
        skills_lower = [s.lower() for s in skills]
        assert skills_lower.count("python") == 1
        assert skills_lower.count("fastapi") == 1

    def test_duplicate_projects_resolved(self):
        """[DeploySense, Deploy Sense] should merge to one project."""
        payload = _valid_profile_data()
        payload["projects"] = [
            {
                "name": "DeploySense",
                "description": "AI monitoring",
                "technologies": ["Python"],
            },
            {
                "name": "Deploy Sense",
                "description": "Deployment tool",
                "technologies": ["Docker"],
            },
        ]
        response = client.post("/profile", json=payload)
        assert response.status_code == 201
        projects = response.json()["data"]["projects"]
        assert len(projects) == 1
        # Technologies should be merged
        techs = [t.lower() for t in projects[0]["technologies"]]
        assert "python" in techs
        assert "docker" in techs


# ─── Test: Completeness Score ────────────────────────────────────────────


class TestCompletenessScore:
    """Tests for profile completeness scoring."""

    def test_completeness_full_profile(self):
        """Full profile should score > 90% (Excellent)."""
        response = client.post("/profile", json=_valid_profile_data())
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["completeness_score"] >= 90
        assert data["profile_status"] == "Excellent"

    def test_completeness_partial_profile(self):
        """Minimal profile (name, email, 1 skill) should score low."""
        payload = {
            "name": "Minimal User",
            "email": "minimal@test.com",
            "skills": ["Python"],
        }
        response = client.post("/profile", json=payload)
        assert response.status_code == 201
        data = response.json()["data"]
        # Only personal info (name + email = 10%) + skills (20%) = ~30%
        assert data["completeness_score"] <= 50
        assert data["profile_status"] in ["Incomplete", "Average"]

    def test_profile_status_mapping(self):
        """Test status thresholds directly."""
        from modules.profile_builder.completeness import get_profile_status

        assert get_profile_status(0) == "Incomplete"
        assert get_profile_status(20) == "Incomplete"
        assert get_profile_status(40) == "Incomplete"
        assert get_profile_status(41) == "Average"
        assert get_profile_status(70) == "Average"
        assert get_profile_status(71) == "Good"
        assert get_profile_status(90) == "Good"
        assert get_profile_status(91) == "Excellent"
        assert get_profile_status(100) == "Excellent"


# ─── Test: Data Normalization ────────────────────────────────────────────


class TestNormalization:
    """Tests for location and degree normalization."""

    def test_location_normalization(self):
        """'Bangalore' should be normalized to 'Bengaluru'."""
        payload = _valid_profile_data()
        payload["location"] = "Bangalore"
        response = client.post("/profile", json=payload)
        assert response.status_code == 201
        assert response.json()["data"]["location"] == "Bengaluru"

    def test_degree_normalization(self):
        """'B.Tech' should be normalized to 'Bachelor of Technology'."""
        payload = _valid_profile_data()
        payload["education"] = [
            {
                "institution": "VIT University",
                "degree": "BE",
                "field_of_study": "Computer Science",
            }
        ]
        # Use a different email to avoid duplicate
        payload["email"] = "degree_test@example.com"
        response = client.post("/profile", json=payload)
        assert response.status_code == 201
        education = response.json()["data"]["education"]
        assert len(education) >= 1
        assert education[0]["degree"] == "Bachelor of Engineering"

    def test_auto_summary_generation(self):
        """Profile without summary should get one auto-generated."""
        payload = _valid_profile_data()
        payload["summary"] = None
        payload["email"] = "summary_test@example.com"
        response = client.post("/profile", json=payload)
        assert response.status_code == 201
        summary = response.json()["data"]["summary"]
        assert summary is not None
        assert len(summary) > 10
        # Should not exceed 150 words
        assert len(summary.split()) <= 150


# ─── Test: Health Check ──────────────────────────────────────────────────


class TestHealthCheck:
    """Test the health check endpoint."""

    def test_health_check(self):
        """GET / should return success."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Talencia" in data["message"]
