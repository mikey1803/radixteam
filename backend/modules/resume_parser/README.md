# Resume Parser Module

Extracts structured Candidate Profile data from PDF and DOCX resume files.

## Architecture

```
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

## Pipeline

```
PDF/DOCX Upload → Text Extraction → LLM Structuring → Stored Result
```

1. **parsers.py** — Extracts raw text using `pdfplumber` (PDF) or `python-docx` (DOCX)
2. **extractor.py** — Sends text to an OpenAI-compatible LLM for structured extraction, with a rule-based fallback
3. **service.py** — Orchestrates validation, extraction, storage, and retrieval
4. **repository.py** — Persists results in Supabase PostgreSQL

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/resume/parse` | Upload and parse a resume |
| `GET` | `/api/v1/resume/parse/{parse_id}` | Retrieve a parse result |
| `GET` | `/api/v1/resume/parses` | List recent parse results |
| `DELETE` | `/api/v1/resume/parse/{parse_id}` | Delete a parse result |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | API key for LLM extraction | Falls back to rule-based extraction |
| `OPENAI_MODEL` | Model name | `gpt-4o-mini` |
| `OPENAI_BASE_URL` | Custom API base URL | OpenAI default |

## Output Format

The parser outputs `ParsedResume` which maps directly to `ProfileBuilder.schemas.ProfileCreate`:

```json
{
  "personal_info": { "first_name": "...", "last_name": "...", "email": "..." },
  "summary": "...",
  "education": [...],
  "experience": [...],
  "skills": [...],
  "projects": [...],
  "certifications": [...],
  "links": [...]
}
```

## Integration with Profile Builder

The parse result can be fed directly into the Profile Builder:

```python
# Upload resume
result = await parser_service.parse_resume(file_bytes, "resume.pdf")

# Feed into profile builder
profile_create = ProfileCreate(**result.parsed_data.model_dump())
profile = await profile_service.create_profile(profile_create)
```

## Supported File Types

- PDF (`.pdf`) — via `pdfplumber`
- DOCX (`.docx`) — via `python-docx`
- Max file size: 10 MB

## Dependencies

- `pdfplumber` — PDF text extraction
- `python-docx` — DOCX text extraction
- `openai` — LLM API client (OpenAI-compatible)
