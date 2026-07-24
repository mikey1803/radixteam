"""Shared exception types for cross-cutting error handling."""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = 500,
        details: Any = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    """Raised when a requested resource is not found."""

    def __init__(
        self, resource: str = "Resource", resource_id: str = ""
    ) -> None:
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=detail, status_code=404)


class ValidationException(AppException):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed", errors: Any = None) -> None:
        super().__init__(message=message, status_code=422, details=errors)


class DuplicateException(AppException):
    """Raised when a duplicate resource is detected."""

    def __init__(self, message: str = "Duplicate resource detected") -> None:
        super().__init__(message=message, status_code=409)


class DatabaseException(AppException):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database operation failed") -> None:
        super().__init__(message=message, status_code=500)
