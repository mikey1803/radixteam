# Profile Builder Module

## Overview

The Profile Builder module transforms parsed resume JSON (from the Resume Parser module) into structured, validated, editable candidate profiles. It is owned by **Developer 3**.

## Architecture

```
POST /profile (Resume JSON)
        │
        ▼
   Validate Fields
        │
        ▼
   Normalize Data (locations, degrees)
        │
        ▼
   Merge & Deduplicate Sections
        │
        ▼
   Generate Summary (if missing)
        │
        ▼
   Calculate Completeness Score
        │
        ▼
   Save Profile (PostgreSQL)
        │
        ▼
   Return Candidate Profile
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/profile` | Create profile from resume JSON |
| `GET` | `/profile/search` | Search profiles (skill, location, education, experience) |
| `GET` | `/profile/{candidate_id}` | Get single profile |
| `PUT` | `/profile/{candidate_id}` | Update profile (partial) |
| `DELETE` | `/profile/{candidate_id}` | Delete profile |

## Example: Create Profile

```bash
curl -X POST http://localhost:8000/profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+91 9876543210",
    "location": "Bangalore",
    "skills": ["Python", "python", "FastAPI", "Docker", "PYTHON"],
    "education": [
      {
        "institution": "VIT University",
        "degree": "B.Tech",
        "field_of_study": "Computer Science",
        "start_date": "2020",
        "end_date": "2024"
      }
    ],
    "experience": [
      {
        "company": "TechCorp",
        "title": "Backend Developer",
        "location": "Bangalore",
        "start_date": "2024-01",
        "description": "Built REST APIs with FastAPI",
        "technologies": ["Python", "FastAPI", "PostgreSQL"]
      }
    ],
    "projects": [
      {
        "name": "DeploySense",
        "description": "AI-powered deployment monitoring",
        "technologies": ["Python", "Docker", "Kubernetes"]
      },
      {
        "name": "Deploy Sense",
        "description": "Deployment monitoring tool",
        "technologies": ["Python", "Docker"]
      }
    ],
    "links": {
      "linkedin": "https://linkedin.com/in/johndoe",
      "github": "https://github.com/johndoe"
    }
  }'
```

### Response

```json
{
  "success": true,
  "message": "Profile created successfully",
  "data": {
    "id": "a1b2c3d4-...",
    "name": "John Doe",
    "email": "john@example.com",
    "location": "Bengaluru",
    "skills": ["Python", "Fastapi", "Docker"],
    "projects": [{"name": "DeploySense", "...": "..."}],
    "completeness_score": 96.67,
    "profile_status": "Excellent",
    "created_at": "2026-07-24T10:00:00"
  },
  "errors": []
}
```

**Note:** "Bangalore" was normalized to "Bengaluru", duplicate skills were merged, and duplicate projects were combined.

## Data Normalization

### Locations
| Input | Normalized |
|-------|-----------|
| Bangalore, B'lore | Bengaluru |
| Bombay | Mumbai |
| Madras | Chennai |
| Calcutta | Kolkata |
| Gurgaon | Gurugram |

### Degrees
| Input | Normalized |
|-------|-----------|
| BE, B.E., B.E | Bachelor of Engineering |
| B.Tech, BTech | Bachelor of Technology |
| MCA, M.C.A | Master of Computer Applications |

## Completeness Scoring

| Section | Weight |
|---------|--------|
| Personal Info (name, email, phone, location) | 20% |
| Skills | 20% |
| Education | 15% |
| Experience | 20% |
| Projects | 15% |
| Certifications | 5% |
| Links | 5% |

### Status Mapping
| Score Range | Status |
|------------|--------|
| 0–40% | Incomplete |
| 41–70% | Average |
| 71–90% | Good |
| 91–100% | Excellent |

## Validation Rules

### Mandatory
- Name (non-empty)
- Email (valid format)
- At least one skill

### Validated
- Email format (RFC regex)
- URL format (linkedin, github, portfolio)
- Candidate ID (UUID4)
- String sanitization (XSS prevention)

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/test_profile_builder.py -v
```

## File Structure

| File | Purpose |
|------|---------|
| `api.py` | FastAPI router — HTTP endpoints |
| `service.py` | Business logic orchestrator |
| `repository.py` | Database access layer |
| `schemas.py` | Pydantic request/response models |
| `models.py` | SQLAlchemy ORM model |
| `validators.py` | Input validation functions |
| `completeness.py` | Completeness scoring engine |
| `merge.py` | Duplicate resolution & merging |
| `utils.py` | Normalization utilities |

## Integration Points

- **Consumes:** Resume Parser module output (JSON)
- **Produces:** Candidate Profile
- **Used by:** Talent Check, Skill Matching, Recruiter Dashboard
