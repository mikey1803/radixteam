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