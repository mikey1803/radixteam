# Talent Match Monorepo

This repository hosts the **AI-powered Talent Match** platform as a scalable monorepo for a 5-developer team.

## Architecture

- `frontend/` — React + Vite client application.
- `backend/` — FastAPI service containing domain modules:
  - `app/jd_analytics/` — job description analytics module.
  - `app/resume_parser/` — resume extraction and parsing module.
  - `app/profile_builder/` — candidate profile construction module.
  - `app/talent_check/` — talent validation and quality checks.
  - `app/skill_matching/` — skill matching and ranking logic.
  - `app/shared/` — shared backend utilities and contracts.
  - `app/main.py` — FastAPI entry point.
  - `tests/` — backend test suite.
- `database/` — database assets and migrations.
- `docs/` — product and technical documentation.
- `.github/` — repository automation and workflows.
- `docker-compose.yml` — local multi-service orchestration placeholder.

## Team Branching Model

Role-specific branches are created for parallel module ownership:

- `role1-jd-analytics`
- `role2-resume-parser`
- `role3-profile-builder`
- `role4-talent-check`
- `role5-skill-matching`
