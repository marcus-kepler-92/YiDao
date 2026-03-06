"""
User schemas

Pydantic models for user-related API requests and responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields"""

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    is_active: bool = Field(default=True, description="是否激活")


class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str = Field(..., min_length=6, description="密码")


class UserUpdate(BaseModel):
    """Schema for updating user information"""

    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    password: Optional[str] = Field(None, min_length=6, description="密码")
    is_active: Optional[bool] = Field(None, description="是否激活")


class UserResponse(UserBase):
    """Schema for user response"""

    id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class UserListQueryParams(BaseModel):
    """
    Query parameters for user list endpoint

    Supports filtering by date ranges, sorting, and search.
    """

    # Date range filters
    created_at_start: Optional[datetime] = Field(
        None, description="创建时间起始（ISO 8601格式）", examples=["2024-01-01T00:00:00Z"]
    )
    created_at_end: Optional[datetime] = Field(
        None, description="创建时间结束（ISO 8601格式）", examples=["2024-12-31T23:59:59Z"]
    )
    updated_at_start: Optional[datetime] = Field(
        None, description="更新时间起始（ISO 8601格式）", examples=["2024-01-01T00:00:00Z"]
    )
    updated_at_end: Optional[datetime] = Field(
        None, description="更新时间结束（ISO 8601格式）", examples=["2024-12-31T23:59:59Z"]
    )

    # Search filters
    username: Optional[str] = Field(
        None, min_length=1, max_length=50, description="用户名搜索（模糊匹配）"
    )
    email: Optional[str] = Field(None, description="邮箱搜索（模糊匹配）")

    # Status filter
    is_active: Optional[bool] = Field(None, description="是否激活")

    # Sorting
    sort_by: Optional[str] = Field(
        default="id",
        description="排序字段（id, created_at, updated_at, username, email）",
        examples=["created_at", "updated_at", "id"],
    )
    sort_order: Optional[str] = Field(
        default="desc", description="排序方向（asc 升序, desc 降序）", examples=["asc", "desc"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "created_at_start": "2024-01-01T00:00:00Z",
                    "created_at_end": "2024-12-31T23:59:59Z",
                    "sort_by": "created_at",
                    "sort_order": "desc",
                },
                {
                    "username": "admin",
                    "is_active": True,
                    "sort_by": "username",
                    "sort_order": "asc",
                },
            ]
        }
    )
