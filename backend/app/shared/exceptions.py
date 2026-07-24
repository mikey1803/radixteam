"""
Shared exception hierarchy, per Chapter 2.13 error handling strategy.
Every error surfaces as one of these categories.
"""


class AppError(Exception):
    """Base class for all handled application errors."""
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
