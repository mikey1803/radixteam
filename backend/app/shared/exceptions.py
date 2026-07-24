"""
Talencia — Shared Exception Classes.

All modules raise these exceptions.
Global exception handlers in main.py convert them to standard API responses.
"""


class TalenciaBaseError(Exception):
    """Base exception for all Talencia errors."""

    def __init__(self, message: str, errors: list[str] | None = None):
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)


class ValidationError(TalenciaBaseError):
    """Raised when input data fails validation."""
    pass


class NotFoundError(TalenciaBaseError):
    """Raised when a requested resource does not exist."""
    pass


class DuplicateError(TalenciaBaseError):
    """Raised when attempting to create a duplicate resource."""
    pass


class DatabaseError(TalenciaBaseError):
    """Raised when a database operation fails."""
    pass
