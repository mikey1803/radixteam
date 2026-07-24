# Profile Builder Module

Converts structured Resume Parser JSON output into a validated, normalised, searchable Candidate Profile.

## Architecture

```
backend/modules/profile_builder/
├── __init__.py          # Module exports
├── api.py               # FastAPI router (CRUD + search endpoints)
├── service.py           # Business logic orchestrator
├── repository.py        # Data-access layer (SQLAlchemy + asyncpg → Supabase)
├── schemas.py           # Pydantic request/response models
├── models.py            # SQLAlchemy ORM model (candidate_profiles table)
├── validators.py        # Input validation rules
├── completeness.py      # Weighted completeness scoring & summary generation
├── merge.py             # Deduplication & merging utilities
├── utils.py             # Normalisation helpers (degree, phone, URL, email, location)
└── README.md            # This file
```

## Endpoints

| Method   | Path                       | Description                  |
| -------- | -------------------------- | ---------------------------- |
| `POST`   | `/profile`                 | Create a new profile         |
| `GET`    | `/profile/{candidate_id}`  | Retrieve a profile           |
| `PUT`    | `/profile/{candidate_id}`  | Update a profile             |
| `DELETE` | `/profile/{candidate_id}`  | Delete a profile             |
| `GET`    | `/profile/search`          | Search with filters          |

## Search Filters

- `skill` — filter by skill name
- `min_experience_years` — minimum total years of experience
- `education_level` — filter by degree level
- `location` — filter by location (partial match)
- `status` — filter by completeness status

## Completeness Scoring

| Section            | Weight |
| ------------------ | ------ |
| Personal Info      | 20 %   |
| Skills             | 20 %   |
| Experience         | 20 %   |
| Education          | 15 %   |
| Projects           | 15 %   |
| Certifications     | 5 %    |
| Links              | 5 %    |

Status mapping: 0–40 Incomplete · 41–70 Average · 71–90 Good · 91–100 Excellent

## Validation

**Required** — name, email, at least one skill
**Recommended** — summary, LinkedIn, GitHub, projects
**Optional** — certifications, portfolio, achievements

## Normalisation

- Skills deduplicated case-insensitively (`Python` / `python` / `PYTHON` → `Python`)
- Degree abbreviations expanded (`BS` → `Bachelor of Science`)
- URLs canonicalised (lowercase scheme/host, trailing slash removed)
- Emails lowercased, phones stripped of formatting
- Location aliases expanded (`SF` → `San Francisco, CA`)

## Dependencies

- `fastapi`
- `pydantic` (with `email-validator`)
- `sqlalchemy[asyncio]`
- `asyncpg`
- `shared/` (exceptions, logging, validators, schemas, constants)

## Database

Requires a `candidate_profiles` table in Supabase PostgreSQL. Create via Alembic migration or execute the schema from `models.py`.
