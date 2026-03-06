from enum import Enum
from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter
from pydantic import BaseModel

from app.tasks import add_task
from app.tasks import app as celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskStatus(str, Enum):
    """Celery 任务状态"""

    PENDING = "PENDING"  # 任务等待中（或任务ID不存在）
    STARTED = "STARTED"  # 任务已开始执行
    SUCCESS = "SUCCESS"  # 任务执行成功
    FAILURE = "FAILURE"  # 任务执行失败
    RETRY = "RETRY"  # 任务重试中
    REVOKED = "REVOKED"  # 任务被取消


class AddRequest(BaseModel):
    x: int
    y: int


class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    result: Any | None = None


@router.post("/add", response_model=TaskResult)
def trigger_task(req: AddRequest):
    """触发异步任务"""
    task = add_task.delay(req.x, req.y)
    return TaskResult(task_id=task.id, status=TaskStatus.PENDING)


@router.get("/{task_id}", response_model=TaskResult)
def get_result(task_id: str):
    """查询任务结果"""
    result = AsyncResult(task_id, app=celery_app)
    return TaskResult(
        task_id=task_id,
        status=TaskStatus(result.status),
        result=result.result if result.ready() else None,
    )
