"""
Exception handlers for FastAPI application

Provides centralized exception handling with consistent response format.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import Response

from .base import AppException

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions"""
    logger.warning(
        f"AppException: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "request_url": str(request.url),
            "request_method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=Response(
            success=False,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            data=None,
        ).model_dump(exclude_none=True),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions (including FastAPI's HTTPException)"""
    return JSONResponse(
        status_code=exc.status_code,
        content=Response(
            success=False, error_code="HTTP_ERROR", message=str(exc.detail), data=None
        ).model_dump(exclude_none=True),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors"""
    errors = exc.errors()
    details = [
        {
            "field": ".".join(str(loc) for loc in e["loc"][1:]),  # Skip 'body' prefix
            "message": e["msg"],
            "type": e["type"],
        }
        for e in errors
    ]

    # Create a human-readable message
    message = "; ".join([f"{d['field']}: {d['message']}" for d in details])

    return JSONResponse(
        status_code=422,
        content=Response(
            success=False,
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
            data=None,
        ).model_dump(exclude_none=True),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    # Try to record error in tracing
    try:
        from app.core.tracing import set_span_error

        set_span_error(exc)
    except Exception:
        pass

    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "request_url": str(request.url),
            "request_method": request.method,
        },
    )

    return JSONResponse(
        status_code=500,
        content=Response(
            success=False, error_code="INTERNAL_ERROR", message="Internal server error", data=None
        ).model_dump(exclude_none=True),
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.debug("Exception handlers configured")
