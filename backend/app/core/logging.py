"""
Talencia — Centralized Logging.

Every request receives a Request ID.
Log format: timestamp | request_id | module | severity | message

Never use print(). Always use get_logger().
"""

import logging
import sys
import uuid
from contextvars import ContextVar

# Context variable to track request IDs across async boundaries
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_ctx.get()


def set_request_id(request_id: str | None = None) -> str:
    """Set a request ID in context. Generates one if not provided."""
    rid = request_id or str(uuid.uuid4())[:8]
    request_id_ctx.set(rid)
    return rid


class RequestIdFilter(logging.Filter):
    """Injects request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def get_logger(module_name: str) -> logging.Logger:
    """
    Return a configured logger for the given module.

    Usage:
        logger = get_logger(__name__)
        logger.info("Profile created", extra={"candidate_id": "abc123"})
    """
    logger = logging.getLogger(module_name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(request_id)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(RequestIdFilter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

    return logger


def setup_logging(level: int = logging.DEBUG) -> None:
    """
    Configure the root logger so third-party/library loggers also emit
    through the request_id format. Optional — get_logger() already
    configures its own logger correctly without this being called.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(request_id)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler.addFilter(RequestIdFilter())
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
