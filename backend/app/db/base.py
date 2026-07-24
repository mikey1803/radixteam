"""
SQLAlchemy declarative base.
All models should import Base from here.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass
