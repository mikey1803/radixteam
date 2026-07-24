# JD Analytics Module

Owner: Developer 1. Nobody else edits this folder (Chapter 4.3).

Converts an uploaded JD (PDF/DOCX) into the shared `ExtractedSkillList`
format (see `app/shared/schemas/skill.py`) so Skill Matching (Role 5) can
consume it directly.

## Endpoints
- `POST /jobs/upload` — multipart file upload
- `GET /jobs` — list all processed JDs
- `GET /jobs/{id}` — fetch one
- `DELETE /jobs/{id}` — remove one

## Pipeline
Upload -> Validate -> Extract Text -> Clean -> AI Prompt -> Normalize Skills -> Save -> Return JSON

## AI mode
Defaults to a deterministic mock (no network/API key needed) via
`AI_PROVIDER_MODE=mock` in `.env`. Switch to `gemini` or `groq` once real
keys are available — nothing in `service.py` needs to change.

## Running just this module's tests
```
cd backend
pytest tests/test_jd_analytics.py -v
```
