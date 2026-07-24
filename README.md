# radixteam

## Repository Structure

This repository follows a feature-oriented layout with three top-level areas:

- `backend/` for FastAPI-style backend services and domain modules.
- `frontend/` for the React + TypeScript frontend.
- `shared/` for reusable core code that must not be duplicated across branches or features.

### Backend

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   ├── dependencies.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── security.py
│   │   └── ai_provider.py
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── migrations/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── shared/
│   └── main.py
├── modules/
│   ├── jd_analytics/
│   ├── resume_parser/
│   ├── profile_builder/
│   ├── talent_check/
│   └── skill_matching/
├── tests/
├── docs/
└── Dockerfile
```

### Frontend

```text
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   ├── services/
│   ├── api/
│   ├── context/
│   ├── layouts/
│   ├── utils/
│   ├── assets/
│   └── App.tsx
├── public/
└── package.json
```

### Shared Core

All cross-cutting code belongs in `shared/` and should be imported from there instead of duplicated in backend or frontend code.

```text
shared/
├── config/
├── constants/
├── schemas/
├── validators/
├── exceptions/
├── logging/
├── security/
├── prompts/
├── utils/
└── ai/
```

### Rule

Nobody duplicates shared core code. If functionality is reused across branches or modules, it belongs in `shared/`.

---

## Running the Backend

### Prerequisites

```bash
pip install fastapi uvicorn pydantic[email-validator] sqlalchemy[asyncio] asyncpg httpx pytest pytest-asyncio pdfplumber python-docx openai
```

### Start the server

From the `backend/` directory:

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server will start at http://127.0.0.1:8000

**Access the API in your browser:**

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000/docs | Swagger UI (Interactive API docs) |
| http://localhost:8000/docs | Swagger UI (alternative) |
| http://127.0.0.1:8000/redoc | ReDoc documentation |

> **Note:** Don't try to access `http://0.0.0.0:8000` - it won't work! Use `http://127.0.0.1:8000` or `http://localhost:8000` instead.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string for Supabase | In-memory mock store |
| `OPENAI_API_KEY` | API key for LLM resume extraction | Falls back to rule-based extraction |
| `OPENAI_MODEL` | Model name for LLM extraction | `gpt-4o-mini` |
| `OPENAI_BASE_URL` | Custom API base URL | OpenAI default |

Example with database:

```bash
set DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Without `DATABASE_URL`, the backend runs with an **in-memory profile store** for development and testing.

### Run Tests

```bash
# From the project root — run all tests
python -m pytest backend/tests/ -v

# Run only profile builder tests
python -m pytest backend/tests/profile_builder/ -v

# Run only resume parser tests
python -m pytest backend/tests/resume_parser/ -v
```

---

## Profile Builder Module

Converts structured Resume Parser JSON output into validated, normalised, searchable Candidate Profiles.

### Module Structure

```text
backend/modules/profile_builder/
├── __init__.py          # Module exports
├── api.py               # FastAPI router (CRUD + search endpoints)
├── service.py           # Business logic orchestrator
├── repository.py        # Data-access layer (SQLAlchemy + asyncpg)
├── schemas.py           # Pydantic request/response models
├── models.py            # SQLAlchemy ORM model (candidate_profiles table)
├── validators.py        # Input validation rules
├── completeness.py      # Weighted completeness scoring & summary generation
├── merge.py             # Deduplication & merging utilities
├── utils.py             # Normalisation helpers (degree, phone, URL, email, location)
└── README.md            # Module documentation
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/profile` | Create a new profile |
| `GET` | `/api/v1/profile/{candidate_id}` | Retrieve a profile |
| `PUT` | `/api/v1/profile/{candidate_id}` | Update a profile |
| `DELETE` | `/api/v1/profile/{candidate_id}` | Delete a profile |
| `GET` | `/api/v1/profile/search` | Search with filters |

### Search Filters

| Parameter | Type | Description |
|-----------|------|-------------|
| `skill` | string | Filter by skill name |
| `min_experience_years` | int | Minimum years of experience |
| `education_level` | string | Filter by degree level |
| `location` | string | Filter by location (partial match) |
| `status` | string | Filter by completeness status |
| `limit` | int | Results per page (1-100, default 20) |
| `offset` | int | Pagination offset |

### Completeness Scoring

| Section | Weight |
|---------|--------|
| Personal Information | 20% |
| Skills | 20% |
| Experience | 20% |
| Education | 15% |
| Projects | 15% |
| Certifications | 5% |
| Links | 5% |

**Status mapping:** 0-40 Incomplete · 41-70 Average · 71-90 Good · 91-100 Excellent

### Validation Rules

- **Required:** name, email, at least one skill
- **Recommended:** summary, LinkedIn, GitHub, projects
- **Optional:** certifications, portfolio, achievements

### Normalisation

- Skills deduplicated case-insensitively (`Python` / `python` / `PYTHON` → `Python`)
- Degree abbreviations expanded (`BS` → `Bachelor of Science`)
- URLs canonicalised (lowercase scheme/host, trailing slash removed)
- Emails lowercased, phones stripped of formatting
- Location aliases expanded (`SF` → `San Francisco, CA`)

---

## Resume Parser Module

Extracts structured Candidate Profile data from PDF and DOCX resume files using text extraction and LLM-based structuring.

### Module Structure

```text
backend/modules/resume_parser/
├── __init__.py          # Module exports
├── api.py               # FastAPI router (parse, retrieve, list, delete)
├── service.py           # Business logic orchestrator
├── repository.py        # Data-access layer
├── schemas.py           # Pydantic models
├── models.py            # SQLAlchemy ORM model
├── parsers.py           # PDF and DOCX text extraction
├── extractor.py         # LLM-based structured extraction
└── README.md
```

### Pipeline

```
PDF/DOCX Upload → Text Extraction → LLM Structuring → Stored Result
```

1. **parsers.py** — Extracts raw text using `pdfplumber` (PDF) or `python-docx` (DOCX)
2. **extractor.py** — Sends text to an OpenAI-compatible LLM for structured extraction, with a rule-based fallback
3. **service.py** — Orchestrates validation, extraction, storage, and retrieval
4. **repository.py** — Persists results in Supabase PostgreSQL

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/resume/parse` | Upload and parse a resume |
| `GET` | `/api/v1/resume/parse/{parse_id}` | Retrieve a parse result |
| `GET` | `/api/v1/resume/parses` | List recent parse results |
| `DELETE` | `/api/v1/resume/parse/{parse_id}` | Delete a parse result |

### Supported File Types

- PDF (`.pdf`) — via `pdfplumber`
- DOCX (`.docx`) — via `python-docx`
- Max file size: 10 MB

### Integration with Profile Builder

The parse result maps directly to `ProfileCreate`:

```python
# Upload resume
result = await parser_service.parse_resume(file_bytes, "resume.pdf")

# Feed into profile builder
profile_create = ProfileCreate(**result.parsed_data.model_dump())
profile = await profile_service.create_profile(profile_create)
```

### Dependencies

```bash
pip install pdfplumber python-docx openai
```
