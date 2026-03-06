"""
审计日志服务

提供审计日志的记录和查询功能
"""

import json
import logging
import time
from functools import wraps
from typing import Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.constants import AuditAction

logger = logging.getLogger(__name__)


# 敏感字段列表（这些字段在记录时会被脱敏）
SENSITIVE_FIELDS = {
    "password",
    "token",
    "secret",
    "api_key",
    "access_token",
    "refresh_token",
    "authorization",
    "credit_card",
    "ssn",
}

# 不需要记录审计日志的路径
EXCLUDED_PATHS = {
    "/health",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/ready",
}


# =============================================================================
# 脱敏工具函数
# =============================================================================


def sanitize_body(body: Optional[str]) -> Optional[str]:
    """脱敏请求体"""
    if not body:
        return None
    try:
        data = json.loads(body)
        return json.dumps(sanitize_dict(data))
    except json.JSONDecodeError:
        return body


def sanitize_dict(data: Optional[Dict]) -> Optional[Dict]:
    """脱敏字典数据"""
    if not data:
        return None
    sanitized = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            sanitized[key] = "***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        else:
            sanitized[key] = value
    return sanitized


# =============================================================================
# AuditMiddleware - 异步审计日志中间件
# =============================================================================


class AuditMiddleware(BaseHTTPMiddleware):
    """
    审计日志中间件

    自动记录所有 API 请求的审计日志
    """

    # HTTP 方法到审计操作的映射
    METHOD_ACTION_MAP = {
        "GET": AuditAction.READ,
        "POST": AuditAction.CREATE,
        "PUT": AuditAction.UPDATE,
        "PATCH": AuditAction.UPDATE,
        "DELETE": AuditAction.DELETE,
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        # 跳过不需要记录的路径
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # 跳过静态文件
        if request.url.path.startswith("/static"):
            return await call_next(request)

        start_time = time.perf_counter()

        # 读取请求体
        request_body = None
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                request_body = body.decode("utf-8") if body else None
            except Exception:
                pass

        # 执行请求
        response = await call_next(request)

        # 计算响应时间
        response_time_ms = int((time.perf_counter() - start_time) * 1000)

        # 异步记录审计日志（不阻塞响应）
        try:
            self._record_audit_log(
                request=request,
                response=response,
                request_body=request_body,
                response_time_ms=response_time_ms,
            )
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")

        return response

    def _record_audit_log(
        self,
        request: Request,
        response: Response,
        request_body: Optional[str],
        response_time_ms: int,
    ) -> None:
        """
        记录审计日志

        使用 Celery 异步任务记录审计日志，避免阻塞事件循环。
        OpenTelemetry 会自动传播 trace context 到 Celery 任务。
        """
        # 获取资源类型和 ID
        resource_type, resource_id = self._extract_resource_info(request.url.path)

        # 获取用户信息（从 request.state 获取，需要认证中间件设置）
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)

        # 获取链路追踪信息
        trace_id = None
        span_id = None
        try:
            from app.core.tracing import get_span_id, get_trace_id

            trace_id = get_trace_id()
            span_id = get_span_id()
        except Exception:
            pass

        # 使用 Celery 异步任务记录审计日志
        # OpenTelemetry 的 CeleryInstrumentor 会自动传播 trace context
        try:
            from app.tasks import record_audit_log_task

            record_audit_log_task.delay(
                action=self.METHOD_ACTION_MAP.get(request.method, AuditAction.READ).value,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                username=username,
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent"),
                method=request.method,
                path=str(request.url.path),
                query_params=str(dict(request.query_params)) if request.query_params else None,
                request_body=request_body,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                trace_id=trace_id,
                span_id=span_id,
            )
        except Exception as e:
            # 如果 Celery 任务提交失败，回退到结构化日志
            logger.warning(
                f"Failed to submit audit log task: {e}, falling back to structured logging"
            )
            logger.info(
                "API Audit",
                extra={
                    "action": self.METHOD_ACTION_MAP.get(request.method, AuditAction.READ).value,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "user_id": user_id,
                    "username": username,
                    "ip_address": self._get_client_ip(request),
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "trace_id": trace_id,
                    "span_id": span_id,
                },
            )

    def _extract_resource_info(self, path: str) -> tuple[str, Optional[str]]:
        """
        从路径中提取资源类型和 ID

        例如：
            /api/v1/users/123 -> ("user", "123")
            /api/v1/users -> ("user", None)
        """
        parts = [p for p in path.split("/") if p]

        # 跳过 api 和版本号
        if len(parts) >= 2 and parts[0] == "api" and parts[1].startswith("v"):
            parts = parts[2:]

        if not parts:
            return "unknown", None

        resource_type = parts[0].rstrip("s")  # users -> user
        resource_id = parts[1] if len(parts) > 1 and parts[1].isdigit() else None

        return resource_type, resource_id

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP"""
        # 优先从代理头获取
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


def audit_log(
    action: AuditAction,
    resource_type: str,
    get_resource_id: Optional[callable] = None,
    get_old_values: Optional[callable] = None,
    get_new_values: Optional[callable] = None,
):
    """
    审计日志装饰器

    用于在 Service 层记录更详细的审计日志（通过 Celery 异步任务）

    用法：
        @audit_log(
            action=AuditAction.UPDATE,
            resource_type="user",
            get_resource_id=lambda args, kwargs: kwargs.get("user_id"),
        )
        async def update_user(self, user_id: int, data: dict):
            ...

    Args:
        action: 操作类型
        resource_type: 资源类型
        get_resource_id: 获取资源 ID 的函数
        get_old_values: 获取变更前值的函数
        get_new_values: 获取变更后值的函数
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取资源 ID
            resource_id = None
            if get_resource_id:
                try:
                    resource_id = get_resource_id(args, kwargs)
                except Exception:
                    pass

            # 获取变更前的值
            old_values = None
            if get_old_values:
                try:
                    old_values = get_old_values(args, kwargs)
                except Exception:
                    pass

            # 执行原函数
            result = await func(*args, **kwargs)

            # 获取变更后的值
            new_values = None
            if get_new_values:
                try:
                    new_values = get_new_values(args, kwargs, result)
                except Exception:
                    pass

            # 使用 Celery 任务异步记录审计日志
            try:
                from app.tasks import record_audit_log_task

                record_audit_log_task.delay(
                    action=action.value if isinstance(action, AuditAction) else action,
                    resource_type=resource_type,
                    resource_id=str(resource_id) if resource_id else None,
                    old_values=sanitize_dict(old_values),
                    new_values=sanitize_dict(new_values),
                )
            except Exception as e:
                logger.error(f"Failed to submit audit log task: {e}")

            return result

        return wrapper

    return decorator
