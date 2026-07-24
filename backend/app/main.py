"""Backend application entrypoint."""

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path

# Ensure the project root is on sys.path so that `shared.*` and
# `backend.*` imports resolve regardless of the working directory.
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Load .env file from project root
from dotenv import load_dotenv

load_dotenv(Path(_project_root) / ".env")

from fastapi import FastAPI

from backend.app.api.router import api_router
from backend.modules.profile_builder.api import set_profile_service
from backend.modules.profile_builder.repository import ProfileRepository
from backend.modules.profile_builder.service import ProfileService
from backend.modules.resume_parser.api import set_parser_service
from backend.modules.resume_parser.repository import ResumeRepository
from backend.modules.resume_parser.service import ResumeParserService

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Application factory."""
    _app = FastAPI(
        title="RadixTeam API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    _app.include_router(api_router)

    @_app.on_event("startup")
    async def _startup() -> None:
        database_url = os.getenv("DATABASE_URL")

        if not database_url:
            logger.warning(
                "DATABASE_URL not set — running with in-memory profile store"
            )
            from unittest.mock import AsyncMock, MagicMock

            from backend.modules.profile_builder.models import CandidateProfile
            from backend.modules.resume_parser.models import ParsedResumeRecord

            _store: dict[str, CandidateProfile] = {}
            _parse_store: dict[str, ParsedResumeRecord] = {}

            repo = MagicMock(spec=ProfileRepository)
            repo.create = AsyncMock(
                side_effect=lambda p: _store.setdefault(p.candidate_id, p) or p
            )
            repo.get_by_id = AsyncMock(
                side_effect=lambda cid: _store.get(cid)
            )
            repo.get_by_email = AsyncMock(
                side_effect=lambda email: next(
                    (p for p in _store.values() if p.email == email), None
                )
            )
            repo.update = AsyncMock(
                side_effect=lambda p: _store.update({p.candidate_id: p}) or p
            )
            repo.delete = AsyncMock(
                side_effect=lambda cid: bool(_store.pop(cid, None))
            )
            repo.search = AsyncMock(
                side_effect=lambda f: list(_store.values())
            )

            parse_repo = MagicMock(spec=ResumeRepository)
            parse_repo.create = AsyncMock(
                side_effect=lambda r: _parse_store.setdefault(r.parse_id, r) or r
            )
            parse_repo.get_by_id = AsyncMock(
                side_effect=lambda pid: _parse_store.get(pid)
            )
            parse_repo.list_records = AsyncMock(
                side_effect=lambda limit=20, offset=0: list(
                    _parse_store.values()
                )[offset : offset + limit]
            )
            parse_repo.delete = AsyncMock(
                side_effect=lambda pid: bool(_parse_store.pop(pid, None))
            )

            set_profile_service(ProfileService(repo))
            set_parser_service(ResumeParserService(parse_repo))
            return

        from sqlalchemy.ext.asyncio import (
            AsyncSession,
            async_sessionmaker,
            create_async_engine,
        )

        from backend.modules.profile_builder.models import Base

        engine = create_async_engine(database_url, echo=False)
        session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            set_profile_service(ProfileService(ProfileRepository(session)))
            set_parser_service(ResumeParserService(ResumeRepository(session)))

        _app.state.db_engine = engine
        _app.state.db_session_factory = session_factory

    @_app.on_event("shutdown")
    async def _shutdown() -> None:
        engine = getattr(_app.state, "db_engine", None)
        if engine:
            await engine.dispose()

    return _app


app = create_app()
