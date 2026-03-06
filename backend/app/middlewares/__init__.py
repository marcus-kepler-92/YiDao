"""
Middlewares module

Provides centralized middleware exports and setup function.
"""

from app.core.audit import AuditMiddleware
from app.core.metrics import PrometheusMiddleware
from app.core.ratelimit import setup_rate_limiting
from app.core.tracing import TracingMiddleware

__all__ = [
    "AuditMiddleware",
    "TracingMiddleware",
    "PrometheusMiddleware",
    "setup_rate_limiting",
    "setup_middlewares",
]


def setup_middlewares(app, settings) -> None:
    """
    Setup all application middlewares

    Middleware execution order (reverse of add order):
    1. CORS (outermost)
    2. Rate Limiting
    3. Tracing
    4. Prometheus Metrics
    5. Audit (innermost)

    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    from fastapi.middleware.cors import CORSMiddleware

    # CORS (processed first, added last)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins or ["*"],
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Audit logging
    app.add_middleware(AuditMiddleware)

    # Prometheus metrics
    if settings.enable_metrics:
        app.add_middleware(PrometheusMiddleware)

    # Tracing (adds trace_id to response)
    app.add_middleware(TracingMiddleware)

    # Rate limiting (must be added after other middlewares)
    if settings.enable_rate_limit:
        setup_rate_limiting(app)
