"""
Talencia — Shared Exception Classes.

All modules raise these exceptions.
Global exception handlers in main.py convert them to standard API responses.

Two hierarchies coexist here: TalenciaBaseError (profile-builder /
skill-matching) and AppError (jd-analytics / resume-parser / talent-check).
Both are wired to handlers in main.py — consolidating them into one is an
intentional follow-up, not something to redesign mid-merge.
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


class AppError(Exception):
    """Base class for all handled application errors (AppError family)."""
    category = "internal_error"
    status_code = 500

    def __init__(self, message: str, errors: list | None = None):
        self.message = message
        self.errors = errors or []
        super().__init__(message)

    def to_response(self) -> dict:
        return {"success": False, "message": self.message, "errors": self.errors}


class ValidationErrorApp(AppError):
    category = "validation_error"
    status_code = 422


class FileErrorApp(AppError):
    category = "file_error"
    status_code = 400


class AIErrorApp(AppError):
    category = "ai_error"
    status_code = 502


class DatabaseErrorApp(AppError):
    category = "database_error"
    status_code = 500


class AuthenticationErrorApp(AppError):
    category = "authentication_error"
    status_code = 401


class NotFoundErrorApp(AppError):
    category = "not_found_error"
    status_code = 404
