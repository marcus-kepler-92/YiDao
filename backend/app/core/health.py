"""
Health check module

Provides health and readiness checks for Kubernetes probes:
- /health (liveness): Is the application running?
- /ready (readiness): Is the application ready to accept traffic?
"""

import logging
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.redis import redis_client

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


@dataclass
class ComponentHealth:
    """Individual component health status"""

    name: str
    status: HealthStatus
    message: str | None = None
    latency_ms: float | None = None


@dataclass
class ReadinessResult:
    """Readiness check result"""

    ready: bool
    status: HealthStatus
    components: list[ComponentHealth]

    def to_dict(self) -> dict:
        return {
            "ready": self.ready,
            "status": self.status.value,
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "latency_ms": c.latency_ms,
                }
                for c in self.components
            ],
        }


async def check_database() -> ComponentHealth:
    """
    Check database connectivity

    Returns:
        ComponentHealth with database status
    """
    import time

    start = time.perf_counter()

    try:
        db = SessionLocal()
        try:
            await db.execute(text("SELECT 1"))
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message="PostgreSQL connection OK",
                latency_ms=round(latency, 2),
            )
        finally:
            await db.close()
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        logger.error(f"Database health check failed: {e}")
        return ComponentHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            message=str(e),
            latency_ms=round(latency, 2),
        )


async def check_redis() -> ComponentHealth:
    """
    Check Redis connectivity

    Returns:
        ComponentHealth with Redis status
    """
    import time

    start = time.perf_counter()

    try:
        if redis_client is None:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message="Redis not connected",
                latency_ms=0,
            )

        await redis_client.ping()
        latency = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            message="Redis connection OK",
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        logger.error(f"Redis health check failed: {e}")
        return ComponentHealth(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=str(e),
            latency_ms=round(latency, 2),
        )


async def check_readiness() -> ReadinessResult:
    """
    Check if application is ready to accept traffic

    Checks all critical dependencies:
    - Database connection
    - Redis connection

    Returns:
        ReadinessResult with overall status and component details
    """
    components = []

    # Check database
    db_health = await check_database()
    components.append(db_health)

    # Check Redis
    redis_health = await check_redis()
    components.append(redis_health)

    # Determine overall status
    unhealthy_count = sum(1 for c in components if c.status == HealthStatus.UNHEALTHY)

    if unhealthy_count == 0:
        overall_status = HealthStatus.HEALTHY
        ready = True
    elif unhealthy_count == len(components):
        overall_status = HealthStatus.UNHEALTHY
        ready = False
    else:
        # Some components are down - degraded but still ready
        # (adjust this logic based on your requirements)
        overall_status = HealthStatus.DEGRADED
        ready = True  # Still accept traffic if DB is up

    # If database is down, we're definitely not ready
    if db_health.status == HealthStatus.UNHEALTHY:
        ready = False

    return ReadinessResult(ready=ready, status=overall_status, components=components)
