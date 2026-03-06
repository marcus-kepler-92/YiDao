"""
System API endpoints

These endpoints are mounted at the application root level,
not under the API version prefix. Includes health checks and app info.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.constants import APP_VERSION
from app.core.config import settings

router = APIRouter(tags=["system"])


@router.get("/", summary="Application Info")
async def root():
    """
    Get application basic information

    Returns:
        dict: Application metadata
    """
    return {
        "app_name": settings.app_name,
        "version": APP_VERSION,
        "environment": settings.app_env,
        "debug": settings.debug,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
    }


@router.get("/health", summary="Liveness Probe")
async def health():
    """
    Liveness check endpoint (Kubernetes Liveness Probe)

    Only checks if the application process is running,
    does not check dependency services.
    Used to determine if the container needs to be restarted.

    Returns:
        dict: Application basic status
    """
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
    }


@router.get("/ready", summary="Readiness Probe")
async def ready():
    """
    Readiness check endpoint (Kubernetes Readiness Probe)

    Checks if the application is ready to accept traffic:
    - Database connection
    - Redis connection

    Returns:
        dict: Readiness status and component health details
    """
    from app.core.health import check_readiness

    result = await check_readiness()

    if not result.ready:
        return JSONResponse(content=result.to_dict(), status_code=503)

    return result.to_dict()
