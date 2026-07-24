"""
Talencia — Shared API Response Schemas.

Standard response contract used by all modules:
{
    "success": true/false,
    "message": "...",
    "data": { ... },
    "errors": []
}
"""

from pydantic import BaseModel
from typing import Any


class APIResponse(BaseModel):
    """Standard API response wrapper used by all endpoints."""
    success: bool
    message: str
    data: Any = None
    errors: list[str] = []
