"""
Talencia — SQLAlchemy Declarative Base.

All ORM models inherit from this Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass
