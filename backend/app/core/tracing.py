"""
OpenTelemetry 链路追踪模块

提供分布式链路追踪功能：
- 自动追踪 HTTP 请求
- 自动追踪数据库查询
- 自动追踪 Redis 操作
- 支持导出到 Jaeger/OTLP
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Span, Status, StatusCode

from app.core.config import settings

logger = logging.getLogger(__name__)

# 全局 Tracer
_tracer: Optional[trace.Tracer] = None


def setup_tracing(app=None) -> None:
    """
    初始化 OpenTelemetry 链路追踪

    Args:
        app: FastAPI 应用实例（可选，用于自动插桩）
    """
    global _tracer

    if not settings.enable_tracing:
        logger.info("Tracing is disabled")
        return

    # 创建资源信息
    resource = Resource.create(
        {
            SERVICE_NAME: settings.app_name,
            SERVICE_VERSION: "1.0.0",
            "deployment.environment": settings.app_env,
        }
    )

    # 创建 TracerProvider
    provider = TracerProvider(resource=resource)

    # 配置导出器
    if settings.app_env == "production":
        # 生产环境：导出到 OTLP (Jaeger/Tempo/等)
        otlp_endpoint = getattr(settings, "otlp_endpoint", "http://localhost:4317")
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info(f"Tracing enabled: OTLP exporter -> {otlp_endpoint}")
    else:
        # 开发环境：输出到控制台（可选）
        if settings.debug:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
            logger.info("Tracing enabled: Console exporter")

    # 设置全局 TracerProvider
    trace.set_tracer_provider(provider)

    # 获取 Tracer
    _tracer = trace.get_tracer(__name__)

    # 自动插桩
    _setup_instrumentors(app)

    logger.info("OpenTelemetry tracing initialized")


def _setup_instrumentors(app=None) -> None:
    """配置自动插桩"""

    # FastAPI 自动插桩
    if app:
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls=f"{settings.prometheus_metrics_path},/health,/docs,/redoc,/openapi.json",
        )
        logger.debug("FastAPI instrumented")

    # SQLAlchemy 自动插桩
    # 注意：对于异步 SQLAlchemy，需要传入引擎实例
    try:
        from app.core.database import engine, sync_engine

        # 插桩异步引擎
        SQLAlchemyInstrumentor().instrument(
            engine=engine.sync_engine,  # asyncpg 引擎的底层同步引擎
            enable_commenter=True,
            service="fastapi-db-async",
        )
        logger.debug("Async SQLAlchemy instrumented")

        # 插桩同步引擎（Celery 使用）
        try:
            SQLAlchemyInstrumentor().instrument(
                engine=sync_engine,
                enable_commenter=True,
                service="fastapi-db-sync",
            )
            logger.debug("Sync SQLAlchemy instrumented")
        except Exception as e:
            logger.warning(f"Failed to instrument sync SQLAlchemy: {e}")

    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")

    # Redis 自动插桩
    try:
        RedisInstrumentor().instrument()
        logger.debug("Redis instrumented")
    except Exception as e:
        logger.warning(f"Failed to instrument Redis: {e}")

    # 日志自动插桩（添加 trace_id 到日志）
    try:
        LoggingInstrumentor().instrument(set_logging_format=True)
        logger.debug("Logging instrumented")
    except Exception as e:
        logger.warning(f"Failed to instrument Logging: {e}")


def get_tracer() -> trace.Tracer:
    """获取 Tracer 实例"""
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer(__name__)
    return _tracer


def get_current_span() -> Optional[Span]:
    """获取当前 Span"""
    return trace.get_current_span()


def get_trace_id() -> Optional[str]:
    """获取当前 Trace ID"""
    span = get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return None


def get_span_id() -> Optional[str]:
    """获取当前 Span ID"""
    span = get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, "016x")
    return None


@contextmanager
def create_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """
    创建一个新的 Span

    用法：
        with create_span("process_order", {"order_id": 123}):
            # 业务逻辑
            pass

    Args:
        name: Span 名称
        attributes: Span 属性
        kind: Span 类型
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def add_span_attributes(attributes: Dict[str, Any]) -> None:
    """
    向当前 Span 添加属性

    Args:
        attributes: 要添加的属性字典
    """
    span = get_current_span()
    if span:
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """
    向当前 Span 添加事件

    Args:
        name: 事件名称
        attributes: 事件属性
    """
    span = get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


def set_span_error(error: Exception) -> None:
    """
    设置当前 Span 为错误状态

    Args:
        error: 异常对象
    """
    span = get_current_span()
    if span:
        span.set_status(Status(StatusCode.ERROR, str(error)))
        span.record_exception(error)


class TracingMiddleware:
    """
    链路追踪中间件

    为每个请求添加 trace_id 到响应头
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                trace_id = get_trace_id()
                if trace_id:
                    headers = list(message.get("headers", []))
                    headers.append((b"x-trace-id", trace_id.encode()))
                    message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
