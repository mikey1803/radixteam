# RadixTeam

## Project Structure

```
radixteam/
├── backend/        ← FastAPI backend (Python)
├── frontend/       ← React + Vite frontend (TypeScript)
├── shared/         ← Shared core utilities
└── README.md
```

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Docs
Once the backend is running, visit: http://localhost:8000/docs