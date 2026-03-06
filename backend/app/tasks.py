"""
Celery 异步任务模块

架构设计：
1. Celery 任务通过 asyncio.run() 运行异步代码，与 FastAPI 保持架构统一
2. 复用异步 Repository 和 Service 层，避免维护两套数据库访问代码
3. 任务应该幂等，可以安全地重试

使用方式：
    @app.task
    def my_task():
        return run_async(async_my_task())

    async def async_my_task():
        async with get_async_db_context() as db:
            # 使用异步数据库操作
            ...
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_failure, task_postrun

from app.core.config import settings
from app.core.metrics import track_celery_task

logger = logging.getLogger(__name__)


def run_async(coro):
    """
    Run async coroutine in sync context.
    Used for running async code within Celery tasks.
    """
    return asyncio.run(coro)


@asynccontextmanager
async def get_async_db_context() -> AsyncGenerator:
    """
    获取异步数据库会话的上下文管理器 (供 Celery 任务使用)

    使用方式:
        async with get_async_db_context() as db:
            result = await db.execute(select(User))
            await db.commit()

    Yields:
        AsyncSession: 异步数据库会话
    """
    from app.core.database import SessionLocal

    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Celery database error: {str(e)}")
            await session.rollback()
            raise


# ============================================================================
# OpenTelemetry Instrumentation
# ============================================================================
try:
    from opentelemetry.instrumentation.celery import CeleryInstrumentor

    # 在导入时立即进行 instrumentation
    # 注意：必须在 Celery app 创建之前调用
    CeleryInstrumentor().instrument()
    logger.info("Celery OpenTelemetry instrumentation enabled")
except ImportError:
    logger.warning("opentelemetry-instrumentation-celery not installed")
except Exception as e:
    logger.warning(f"Failed to instrument Celery: {e}")

app = Celery(
    "fastapi_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.timezone,
    enable_utc=True,
    task_track_started=True,
    task_always_eager=settings.celery_task_always_eager,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    task_time_limit=settings.celery_task_time_limit,
    worker_prefetch_multiplier=1,
    # Beat 调度文件存储位置（解决 Docker 权限问题）
    beat_schedule_filename="/tmp/celerybeat-schedule",
    # Beat 定时任务配置
    beat_schedule={
        # 每天早上 9 点执行
        "daily-report": {
            "task": "app.tasks.daily_report_task",
            "schedule": crontab(hour=9, minute=0),
        },
        # 每小时更新用户指标
        "update-user-metrics": {
            "task": "app.tasks.update_user_metrics_task",
            "schedule": crontab(minute=0),  # 每小时整点
        },
    },
)


# ============================================================================
# Celery 信号处理（用于监控）
# ============================================================================


@task_postrun.connect
def task_postrun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kw
):
    """任务执行成功后"""
    track_celery_task(task.name, "success")
    logger.info(f"Task {task.name} completed: {task_id}")


@task_failure.connect
def task_failure_handler(
    sender=None,
    task_id=None,
    exception=None,
    args=None,
    kwargs=None,
    traceback=None,
    einfo=None,
    **kw,
):
    """任务执行失败后"""
    track_celery_task(sender.name, "failure")
    logger.error(f"Task {sender.name} failed: {task_id}, error: {exception}")


@app.task
def add_task(x: int, y: int) -> int:
    """最简单的任务：两数相加"""
    import time

    time.sleep(3)  # 模拟耗时操作
    return x + y


@app.task
def daily_report_task():
    """每日报告任务：每天早上 9 点执行"""
    from datetime import datetime

    logger.info(f"Daily report generated at {datetime.now()}")
    # TODO: 在这里添加实际的报告逻辑
    return {"status": "ok", "time": str(datetime.now())}


@app.task(bind=True, max_retries=3)
def record_audit_log_task(
    self,
    action: str,
    resource_type: str,
    resource_id: str = None,
    user_id: int = None,
    username: str = None,
    ip_address: str = None,
    user_agent: str = None,
    method: str = None,
    path: str = None,
    query_params: str = None,
    request_body: str = None,
    status_code: int = None,
    response_time_ms: int = None,
    old_values: dict = None,
    new_values: dict = None,
    trace_id: str = None,
    span_id: str = None,
    extra: dict = None,
):
    """
    异步记录审计日志任务

    在高流量场景下，通过 Celery 异步记录审计日志，避免阻塞 API 响应
    """

    async def _record_audit_log():
        from app.models.audit_log import AuditLog

        async with get_async_db_context() as db:
            audit_log = AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                method=method,
                path=path,
                query_params=query_params,
                request_body=request_body,
                status_code=status_code,
                response_time_ms=response_time_ms,
                old_values=old_values,
                new_values=new_values,
                trace_id=trace_id,
                span_id=span_id,
                extra=extra,
            )

            db.add(audit_log)
            await db.flush()  # 获取 ID
            logger.debug(f"Audit log recorded: {action} {resource_type} {resource_id}")
            return {"status": "success", "id": audit_log.id}

    try:
        return run_async(_record_audit_log())
    except Exception as exc:
        logger.error(f"Failed to record audit log: {exc}")
        # 重试任务（最多 3 次）
        raise self.retry(exc=exc, countdown=60)  # 60 秒后重试


@app.task
def update_user_metrics_task():
    """
    更新用户指标任务：每小时执行

    统计活跃/非活跃/已删除用户数，更新到 Prometheus 指标
    """

    async def _update_user_metrics():
        from sqlalchemy import func, select

        from app.core.metrics import update_user_metrics
        from app.models.user import User

        async with get_async_db_context() as db:
            # 统计活跃用户（未删除）
            active_result = await db.execute(
                select(func.count(User.id)).where(
                    User.deleted_at.is_(None),
                    User.is_active == True,  # noqa: E712
                )
            )
            active_count = active_result.scalar() or 0

            # 统计非活跃用户（未删除但不活跃）
            inactive_result = await db.execute(
                select(func.count(User.id)).where(
                    User.deleted_at.is_(None),
                    User.is_active == False,  # noqa: E712
                )
            )
            inactive_count = inactive_result.scalar() or 0

            # 统计已删除用户
            deleted_result = await db.execute(
                select(func.count(User.id)).where(User.deleted_at.is_not(None))
            )
            deleted_count = deleted_result.scalar() or 0

            # 更新 Prometheus 指标
            update_user_metrics(active=active_count, inactive=inactive_count, deleted=deleted_count)

            logger.info(
                f"User metrics updated: active={active_count}, "
                f"inactive={inactive_count}, deleted={deleted_count}"
            )

            return {
                "status": "success",
                "active": active_count,
                "inactive": inactive_count,
                "deleted": deleted_count,
            }

    try:
        return run_async(_update_user_metrics())
    except Exception as exc:
        logger.error(f"Failed to update user metrics: {exc}")
        raise


@app.task(bind=True, max_retries=3)
def send_email_task(self, to: str, subject: str, body: str):
    """
    发送邮件任务（示例）

    Args:
        to: 收件人邮箱
        subject: 邮件主题
        body: 邮件内容
    """
    try:
        # TODO: 实现真实的邮件发送逻辑
        import time

        time.sleep(2)  # 模拟发送邮件
        logger.info(f"Email sent to {to}: {subject}")
        return {"status": "success", "to": to}
    except Exception as exc:
        logger.error(f"Failed to send email: {exc}")
        raise self.retry(exc=exc, countdown=300)  # 5 分钟后重试
