"""
Common FastAPI dependencies used across routes.
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db as _get_db


def get_db() -> Generator[Session, None, None]:
    """Re-export get_db from session for convenience."""
    yield from _get_db()
