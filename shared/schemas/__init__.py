"""Shared Pydantic response schemas."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardised API envelope used by every endpoint."""

    success: bool = True
    message: str = "OK"
    data: T | None = None
    errors: Any = None
    request_id: str | None = None
