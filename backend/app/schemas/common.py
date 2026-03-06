from __future__ import annotations

from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    """
    通用 API 响应格式

    所有 API 接口返回的统一格式，包含成功状态、消息和数据
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "操作成功",
                    "data": {"id": 1, "name": "示例"},
                    "error_code": None,
                    "details": None,
                },
                {
                    "success": False,
                    "message": "参数错误",
                    "data": None,
                    "error_code": "VALIDATION_ERROR",
                    "details": [{"field": "email", "message": "invalid"}],
                },
            ]
        }
    )

    success: bool = Field(default=True, description="请求是否成功")
    message: str = Field(
        default="success", description="响应消息", examples=["操作成功", "创建成功", "更新成功"]
    )
    error_code: str | None = Field(
        default=None, description="错误代码", examples=["VALIDATION_ERROR", "NOT_FOUND"]
    )
    details: Any | None = Field(default=None, description="错误详情")
    data: T | None = Field(default=None, description="响应数据")


class PaginatedData(BaseModel, Generic[T]):
    """
    分页数据结构

    包含数据列表和分页元信息
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"list": [{"id": 1, "name": "项目1"}], "current": 1, "pageSize": 10, "total": 100}
            ]
        }
    )

    list: List[T] = Field(..., description="数据列表")
    current: int = Field(..., ge=1, description="当前页码", examples=[1])
    pageSize: int = Field(..., ge=1, le=100, description="每页数量", examples=[10])
    total: int = Field(..., ge=0, description="总记录数", examples=[100])


class PaginatedResponse(Response[PaginatedData[T]], Generic[T]):
    """
    分页响应格式

    继承通用响应格式，data 字段为分页数据结构
    """

    pass


class PaginationParams(BaseModel):
    """
    分页查询参数

    用于 GET 请求的分页参数，支持自动验证和文档生成
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"current": 1, "pageSize": 10}, {"current": 2, "pageSize": 20}]
        }
    )

    current: int = Field(default=1, ge=1, description="当前页码，从1开始", examples=[1])
    pageSize: int = Field(
        default=10, ge=1, le=100, description="每页数量，最大100", examples=[10, 20, 50]
    )

    @property
    def offset(self) -> int:
        """计算数据库查询的偏移量"""
        return (self.current - 1) * self.pageSize

    @property
    def limit(self) -> int:
        """获取查询限制数量（别名）"""
        return self.pageSize
