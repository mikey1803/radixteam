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

## Running the backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # or your preferred env tool
pip install -r requirements.txt
cp .env.example .env          # AI_PROVIDER_MODE=mock by default — no keys needed
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/health` — should return
`{"success": true, "data": {"status": "ok", "ai_mode": "mock"}}`.

Interactive API docs: `http://localhost:8000/docs`.

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. Five tabs, one per role.

## Running tests

```bash
cd backend
pytest tests/ -v
```

(Tests require the packages in `requirements.txt` — `fastapi`, `PyMuPDF`,
etc. This sandbox couldn't reach the internet to install them, so verify
locally; the logic itself was verified here with dependency-free unit
checks — normalization, mock AI extraction, text cleaning, and fuzzy
matching all pass.)

## What's real vs. stub

| Module | Status | Notes |
|---|---|---|
| JD Analytics | ✅ Fully built | Upload, validate, extract (PyMuPDF/pdfplumber/python-docx), clean, AI-extract, normalize, persist, full CRUD API, unit tests |
| Profile Builder | ✅ Fully built | Real CRUD, merge, completeness scoring, validators |
| Skill Matching | ✅ Fully built | Full staged matching pipeline, adapters, innovation layer, extensive tests |
| Resume Parser | 🟡 Stub (as of this merge) | Superseded once `feature/resume-parser` merges |
| Talent Check | 🟡 Stub (as of this merge) | Superseded once `feature/talent-check` merges |

Each stub module's own `README.md` (in `backend/modules/<name>/`) has
specific notes for whoever picks it up.

## AI Provider

Everything defaults to a deterministic **mock AI** (`AI_PROVIDER_MODE=mock`
in `.env`) so nobody needs real API keys to build or demo today. When keys
are available, set `AI_PROVIDER_MODE=gemini` (or `groq`) and fill in
`GEMINI_API_KEY` / `GROQ_API_KEY` — no service-layer code changes needed;
see `backend/app/shared/ai/provider.py`.

## Folder structure

```
backend/
  app/
    api/            # router aggregation, request-id middleware
    core/           # config, logging
    shared/         # THE shared data contract (schemas/skill.py), AI provider, JSON file storage
    main.py
  modules/
    jd_analytics/    # fully built
    resume_parser/   # stub (until feature/resume-parser merges)
    profile_builder/ # fully built
    talent_check/    # stub (until feature/talent-check merges)
    skill_matching/  # fully built
  tests/
  requirements.txt
  Dockerfile
  .env.example

frontend/
  src/
    api/client.ts    # shared fetch client, one per module
    pages/           # one page per role (5 tabs)
    App.tsx

shared/
  data_contract.md   # human-readable mirror of the Pydantic/TS contract — predates the real
                      # schemas below and no longer matches them; treat modules/*/schemas.py
                      # as ground truth, not this file
```
