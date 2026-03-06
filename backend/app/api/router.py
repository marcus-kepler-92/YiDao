"""
API Router Registration

Centralizes all API route registration.
"""

from fastapi import FastAPI

from app.api.system import router as system_router
from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.metrics import metrics_endpoint


def register_routers(app: FastAPI) -> None:
    """
    Register all API routers with the application

    Structure:
        /                   - System endpoints (health, info)
        /api/v1/users       - User management
        /api/v1/tasks       - Task management
        /metrics            - Prometheus metrics

    Args:
        app: FastAPI application instance
    """
    # System endpoints (/, /health, /ready)
    app.include_router(system_router)

    # API v1 endpoints
    app.include_router(v1_router, prefix=settings.api_prefix_v1)

    # Prometheus metrics endpoint
    if settings.enable_metrics:
        app.add_api_route(
            settings.prometheus_metrics_path,
            metrics_endpoint,
            methods=["GET"],
            tags=["monitoring"],
            include_in_schema=False,
        )
