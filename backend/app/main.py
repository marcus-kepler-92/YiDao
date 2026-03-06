"""
FastAPI Application Entry Point

This module creates and configures the FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app.api.router import register_routers
from app.constants import APP_VERSION
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.logger import get_logger, setup_logging
from app.core.redis import close_redis, init_redis, redis_client
from app.core.tracing import setup_tracing
from app.exceptions import setup_exception_handlers
from app.middlewares import setup_middlewares

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""

    # =========== Startup ===========
    logger.info("=" * 60)
    logger.info("Application Starting")
    logger.info("=" * 60)
    logger.info(f"App: {settings.app_name} v{APP_VERSION}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug: {settings.debug}")
    logger.info(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    logger.info(f"Redis: {settings.redis_host}:{settings.redis_port}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise

    # Initialize Redis & Cache
    try:
        await init_redis()
        FastAPICache.init(RedisBackend(redis_client), prefix="app:")
        logger.info("FastAPICache initialized with Redis backend")
    except Exception as e:
        logger.warning(f"Failed to initialize Resis/Cache: {str(e)}")

    # Initialize tracing
    try:
        setup_tracing(app)
        logger.info("OpenTelemetry tracing initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize tracing: {str(e)}")

    # =========== Application Ready ===========
    logger.info("=" * 60)
    logger.info("Application is ready to accept requests")
    logger.info("=" * 60)
    logger.info(f"API Docs: http://{settings.app_host}:{settings.app_port}/docs")
    logger.info(f"Health:   http://{settings.app_host}:{settings.app_port}/health")
    logger.info(
        f"Metrics:  http://{settings.app_host}:{settings.app_port}{settings.prometheus_metrics_path}"
    )
    logger.info("=" * 60)

    yield  # Application running...

    # =========== Shutdown ===========
    logger.info("=" * 60)
    logger.info("Application Shutting Down")
    logger.info("=" * 60)

    # Clear FastAPI Cache
    try:
        await FastAPICache.clear()
        logger.info("FastAPICache cleared")
    except Exception as e:
        logger.warning(f"Failed to clear FastAPICache: {str(e)}")

    # Close Redis
    await close_redis()

    # Close database connections
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}", exc_info=True)


def create_app() -> FastAPI:
    """
    Application factory

    Creates and configures a FastAPI application instance.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title=settings.app_name,
        version=APP_VERSION,
        description="YiDao 易道 — 对话式生活分析与教练助手 API",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Setup middlewares
    setup_middlewares(app, settings)
    logger.debug("Middlewares configured")

    # Setup exception handlers
    setup_exception_handlers(app)
    logger.debug("Exception handlers configured")

    # Register routers
    register_routers(app)
    logger.debug("Routes registered")

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
