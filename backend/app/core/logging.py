"""
Centralized logging — per Chapter 2.12. Never use print().

Every request gets a request_id (attached by middleware in main.py) so logs
can be correlated end-to-end: Upload -> Extraction -> AI Call ->
Normalization -> Save -> Success.
"""
import logging
import sys

_LOG_FORMAT = "%(asctime)s | %(request_id)s | %(name)s | %(levelname)s | %(message)s"


class _RequestIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    handler.addFilter(_RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.addFilter(_RequestIdFilter())
    return logger
