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

from typing import Any

from pydantic import BaseModel



class APIResponse(BaseModel):
    """Standard API response wrapper used by all endpoints."""
    success: bool
    message: str
    data: Any = None
    errors: list[str] = []
