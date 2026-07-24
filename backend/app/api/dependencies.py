"""Shared FastAPI dependencies (request id, etc.)."""
import uuid

from fastapi import Request


def get_request_id(request: Request) -> str:
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return rid
