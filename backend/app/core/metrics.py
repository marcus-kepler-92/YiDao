"""
Prometheus 指标模块

提供应用级别的监控指标：
- HTTP 请求计数、延迟、状态码分布
- 数据库连接池状态
- Redis 连接状态
- 业务指标（用户数等）
"""

import logging
import time
from functools import wraps
from typing import Callable

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# 应用信息
# ============================================================================

APP_INFO = Info("app", "Application information")
APP_INFO.info(
    {
        "name": settings.app_name,
        "env": settings.app_env,
        "version": "1.0.0",
    }
)

# ============================================================================
# HTTP 请求指标
# ============================================================================

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total", "Total number of HTTP requests", ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress", "Number of HTTP requests in progress", ["method", "endpoint"]
)

# ============================================================================
# 数据库指标
# ============================================================================

DB_CONNECTIONS_TOTAL = Gauge("db_connections_total", "Total number of database connections in pool")

DB_CONNECTIONS_ACTIVE = Gauge("db_connections_active", "Number of active database connections")

DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# ============================================================================
# Redis 指标
# ============================================================================

REDIS_CONNECTIONS_ACTIVE = Gauge("redis_connections_active", "Number of active Redis connections")

REDIS_OPERATION_DURATION_SECONDS = Histogram(
    "redis_operation_duration_seconds",
    "Redis operation duration in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
)

CACHE_HITS_TOTAL = Counter("cache_hits_total", "Total number of cache hits")

CACHE_MISSES_TOTAL = Counter("cache_misses_total", "Total number of cache misses")

# ============================================================================
# 业务指标
# ============================================================================

USERS_TOTAL = Gauge(
    "users_total",
    "Total number of users",
    ["status"],  # active, inactive, deleted
)

TASKS_TOTAL = Counter(
    "celery_tasks_total",
    "Total number of Celery tasks",
    ["task_name", "status"],  # success, failure, retry
)


# ============================================================================
# Prometheus 中间件
# ============================================================================


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Prometheus 指标收集中间件

    自动收集每个请求的：
    - 请求计数
    - 请求延迟
    - 进行中请求数
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过指标端点本身
        if request.url.path == settings.prometheus_metrics_path:
            return await call_next(request)

        method = request.method
        # 规范化路径（将路径参数替换为占位符）
        endpoint = self._normalize_path(request.url.path)

        # 增加进行中请求计数
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

        start_time = time.perf_counter()
        status_code = 500  # 默认状态码

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
        finally:
            # 记录请求延迟
            duration = time.perf_counter() - start_time
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)

            # 增加请求计数
            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()

            # 减少进行中请求计数
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

    def _normalize_path(self, path: str) -> str:
        """
        规范化路径，将数字 ID 替换为占位符

        例如：/api/v1/users/123 -> /api/v1/users/{id}
        """
        parts = path.split("/")
        normalized = []
        for part in parts:
            if part.isdigit():
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/".join(normalized)


# ============================================================================
# 指标端点
# ============================================================================


async def metrics_endpoint(request: Request) -> Response:
    """Prometheus 指标端点"""
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


# ============================================================================
# 辅助函数
# ============================================================================


def track_db_query(operation: str):
    """
    数据库查询耗时追踪装饰器

    用法：
        @track_db_query("select")
        def find_user(user_id: int):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start_time
                DB_QUERY_DURATION_SECONDS.labels(operation=operation).observe(duration)

        return wrapper

    return decorator


def track_cache_hit():
    """记录缓存命中"""
    CACHE_HITS_TOTAL.inc()


def track_cache_miss():
    """记录缓存未命中"""
    CACHE_MISSES_TOTAL.inc()


def update_user_metrics(active: int, inactive: int, deleted: int):
    """更新用户指标"""
    USERS_TOTAL.labels(status="active").set(active)
    USERS_TOTAL.labels(status="inactive").set(inactive)
    USERS_TOTAL.labels(status="deleted").set(deleted)


def track_celery_task(task_name: str, status: str):
    """记录 Celery 任务执行"""
    TASKS_TOTAL.labels(task_name=task_name, status=status).inc()
