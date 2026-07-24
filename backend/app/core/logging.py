"""
Structured logging configuration for the application.
"""

import logging
import sys

from app.core.config import get_settings


def setup_logging() -> logging.Logger:
    """Configure and return the application logger."""
    settings = get_settings()

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
    )

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger(settings.APP_NAME)
    logger.info("Logging initialised — level=%s", settings.LOG_LEVEL)
    return logger


# Module-level convenience logger
logger = setup_logging()
