from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from app.core.ratelimit import limiter
from app.dependencies import PaginationParams, get_pagination, get_user_service
from app.schemas.common import PaginatedData, PaginatedResponse, Response
from app.schemas.user import UserCreate, UserListQueryParams, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=Response[UserResponse], status_code=201)
@limiter.limit("10/minute")  # 限制每分钟最多创建 10 个用户
async def add_user(
    request: Request,  # Rate limiter 需要 request 参数
    user: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """创建用户"""
    return Response(data=await service.create_user(user), message="创建成功")


@router.get("/deleted", response_model=PaginatedResponse[UserResponse])
async def get_deleted_user_list(
    pagination: PaginationParams = Depends(get_pagination),
    service: UserService = Depends(get_user_service),
):
    """获取已删除的用户列表（分页）"""
    users, total = await service.get_deleted_users(pagination.current, pagination.pageSize)
    return PaginatedResponse(
        data=PaginatedData(
            list=users, current=pagination.current, pageSize=pagination.pageSize, total=total
        )
    )


@router.get("/{user_id}", response_model=Response[UserResponse])
async def get_user_detail(user_id: int, service: UserService = Depends(get_user_service)):
    """获取单个用户"""
    return Response(data=await service.get_user(user_id))


@router.get("", response_model=PaginatedResponse[UserResponse])
async def get_user_list(
    pagination: PaginationParams = Depends(get_pagination),
    # Query filters
    created_at_start: Optional[datetime] = Query(None, description="创建时间起始"),
    created_at_end: Optional[datetime] = Query(None, description="创建时间结束"),
    updated_at_start: Optional[datetime] = Query(None, description="更新时间起始"),
    updated_at_end: Optional[datetime] = Query(None, description="更新时间结束"),
    username: Optional[str] = Query(
        None, min_length=1, max_length=50, description="用户名搜索（模糊匹配）"
    ),
    email: Optional[str] = Query(None, description="邮箱搜索（模糊匹配）"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    sort_by: Optional[str] = Query(
        "id", description="排序字段（id, created_at, updated_at, username, email）"
    ),
    sort_order: Optional[str] = Query("desc", description="排序方向（asc, desc）"),
    service: UserService = Depends(get_user_service),
):
    """
    获取用户列表（分页）

    支持按创建时间、更新时间范围过滤，用户名/邮箱搜索，以及排序。
    """
    query_params = UserListQueryParams(
        created_at_start=created_at_start,
        created_at_end=created_at_end,
        updated_at_start=updated_at_start,
        updated_at_end=updated_at_end,
        username=username,
        email=email,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    users, total = await service.get_user_list(
        current=pagination.current, pageSize=pagination.pageSize, query_params=query_params
    )

    return PaginatedResponse(
        data=PaginatedData(
            list=users, current=pagination.current, pageSize=pagination.pageSize, total=total
        )
    )


@router.put("/{user_id}", response_model=Response[UserResponse])
async def update_user_by_id(
    user_id: int, user_update: UserUpdate, service: UserService = Depends(get_user_service)
):
    """更新用户"""
    return Response(data=await service.update_user(user_id, user_update), message="更新成功")


@router.delete("/{user_id}", response_model=Response)
async def remove_user_by_id(user_id: int, service: UserService = Depends(get_user_service)):
    """删除用户（软删除）"""
    await service.delete_user(user_id)
    return Response(message="删除成功")


@router.post("/{user_id}/restore", response_model=Response[UserResponse])
async def restore_user_by_id(user_id: int, service: UserService = Depends(get_user_service)):
    """恢复已删除的用户"""
    return Response(data=await service.restore_user(user_id), message="恢复成功")
