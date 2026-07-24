# RADIX Talent Match — Setup & Integration Guide

This adds a working backend (FastAPI) + frontend (React) for the whole
Talent Match Hackathon flow: **JD Analytics is fully built**; Resume Parser,
Profile Builder, Talent Check, and Skill Matching are **working stubs**
your teammates can extend without breaking anything you've built.

## How to merge this into your existing branch

You already have `backend/`, `frontend/`, `shared/` scaffolded on
`feature/jd-analytics`. Copy these files in on top of / alongside what's
there:

```bash
# from inside your local clone of radixteam, on feature/jd-analytics
cp -r /path/to/this/output/backend/* backend/
cp -r /path/to/this/output/frontend/* frontend/
cp -r /path/to/this/output/shared/* shared/
git add -A
git commit -m "Add JD Analytics module (full) + stubs for other 4 roles"
git push
```

If your existing `backend/`/`frontend`/`shared` folders already have files
with the same names, review the diff before overwriting — your prior
scaffold and this one may define overlapping things (e.g. an existing
`README.md`).

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
| **JD Analytics** (yours) | ✅ Fully built | Upload, validate, extract (PyMuPDF/pdfplumber/python-docx), clean, AI-extract, normalize, persist, full CRUD API, unit tests |
| Resume Parser | 🟡 Stub | Returns mock `ExtractedSkillList`; reuse `jd_analytics/parser.py`'s extraction functions |
| Profile Builder | 🟢 Functional stub | Real save/load CRUD; needs the React form UI fleshed out |
| Talent Check | 🟢 Functional stub | Real gap/readiness scoring logic; needs `talent_check_company_skillsets.json` from your facilitator |
| Skill Matching | 🟢 Functional stub | Real fuzzy string matching; can be upgraded to AI-based semantic matching later |

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
    jd_analytics/    # <- your module, fully built
    resume_parser/   # stub
    profile_builder/ # functional stub
    talent_check/    # functional stub
    skill_matching/  # functional stub
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
  data_contract.md   # human-readable mirror of the Pydantic/TS contract
```
