"""Structured logging framework for cross-cutting log concerns."""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Return the current request ID or generate one."""
    rid = request_id_var.get()
    if not rid:
        rid = str(uuid.uuid4())
        request_id_var.set(rid)
    return rid


class StructuredLogger:
    """Logger that attaches structured context to every record."""

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def _emit(self, level: int, event: str, **kwargs: Any) -> None:
        extra: dict[str, Any] = {
            "event": event,
            "request_id": get_request_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }
        self._logger.log(level, event, extra=extra)

    def info(self, event: str, **kwargs: Any) -> None:
        self._emit(logging.INFO, event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._emit(logging.WARNING, event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._emit(logging.ERROR, event, **kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._emit(logging.DEBUG, event, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """Factory for a named structured logger."""
    return StructuredLogger(name)
