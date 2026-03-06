"""
Rate Limiting Module

Provides API rate limiting using slowapi (based on limits library).

Features:
- Per-IP rate limiting
- Redis backend for distributed rate limiting
- Configurable limits per endpoint
- Custom rate limit exceeded response
"""

import logging
from functools import lru_cache

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.

    Handles X-Forwarded-For header for proxied requests.
    """
    # Check for forwarded IP (when behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded.split(",")[0].strip()

    # Check for real IP header (Nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct connection IP
    return get_remote_address(request)


def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.

    Returns a JSON response with rate limit information.
    """
    logger.warning(f"Rate limit exceeded for {get_client_ip(request)}: {exc.detail}")

    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail),
        },
        headers={
            "Retry-After": str(exc.retry_after) if hasattr(exc, "retry_after") else "60",
            "X-RateLimit-Limit": request.state.view_rate_limit
            if hasattr(request.state, "view_rate_limit")
            else "",
        },
    )


@lru_cache()
def get_limiter() -> Limiter:
    """
    Get or create the rate limiter instance.

    Uses Redis as storage backend if available, otherwise falls back to memory.
    """
    # Use Redis for distributed rate limiting if configured
    storage_uri = None
    if settings.redis_host:
        # 使用独立的 Redis DB (4) 用于限流，避免与其他功能冲突
        redis_password_part = f":{settings.redis_password}@" if settings.redis_password else ""
        storage_uri = f"redis://{redis_password_part}{settings.redis_host}:{settings.redis_port}/4"

    limiter = Limiter(
        key_func=get_client_ip,
        default_limits=[settings.rate_limit_default] if settings.enable_rate_limit else [],
        storage_uri=storage_uri,
        strategy="fixed-window",  # or "moving-window" for more precise limiting
    )

    return limiter


# Global limiter instance
limiter = get_limiter()


# =============================================================================
# Rate Limit Decorators
# =============================================================================
# Usage:
#   from app.core.ratelimit import limiter
#
#   @router.get("/endpoint")
#   @limiter.limit("10/minute")
#   async def my_endpoint(request: Request):
#       ...
#
# Common rate limit patterns:
#   - "10/minute" - 10 requests per minute
#   - "100/hour" - 100 requests per hour
#   - "5/second" - 5 requests per second
#   - "1000/day" - 1000 requests per day
# =============================================================================


# =============================================================================
# Middleware Setup
# =============================================================================


def setup_rate_limiting(app):
    """
    Setup rate limiting for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    logger.info("Rate limiting middleware initialized")
