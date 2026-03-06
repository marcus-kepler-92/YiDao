"""
Base exception classes

Provides a hierarchy of application exceptions with standardized error codes.
"""

from typing import Any


class AppException(Exception):
    """
    Base application exception

    All custom exceptions should inherit from this class.
    """

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(
        self, message: str | None = None, error_code: str | None = None, details: Any = None
    ):
        self.message = message or self.message
        self.error_code = error_code or self.error_code
        self.details = details
        super().__init__(self.message)


class BadRequestException(AppException):
    """400 Bad Request - Invalid input or request format"""

    status_code = 400
    error_code = "BAD_REQUEST"
    message = "Invalid request"


class UnauthorizedException(AppException):
    """401 Unauthorized - Authentication required or failed"""

    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Authentication required"


class ForbiddenException(AppException):
    """403 Forbidden - Authenticated but not authorized"""

    status_code = 403
    error_code = "FORBIDDEN"
    message = "Access denied"


class NotFoundException(AppException):
    """404 Not Found - Resource does not exist"""

    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"


class ConflictException(AppException):
    """409 Conflict - Resource already exists or state conflict"""

    status_code = 409
    error_code = "CONFLICT"
    message = "Resource conflict"


class ValidationException(AppException):
    """422 Unprocessable Entity - Validation failed"""

    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Validation failed"


class InternalServerException(AppException):
    """500 Internal Server Error - Unexpected server error"""

    status_code = 500
    error_code = "INTERNAL_ERROR"
    message = "Internal server error"
