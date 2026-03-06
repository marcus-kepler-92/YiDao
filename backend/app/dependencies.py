"""
Centralized dependency injection

All FastAPI dependencies are defined here for consistency and reusability.
"""

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.repository.pattern_skill_repository import PatternSkillRepository
from app.repository.user_repository import UserRepository
from app.schemas.common import PaginationParams
from app.services.auth_service import AuthService
from app.services.pattern_skill_service import PatternSkillService
from app.services.user_service import UserService

# =============================================================================
# Pagination Dependencies
# =============================================================================


def get_pagination(
    current: int = Query(1, ge=1, description="当前页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
) -> PaginationParams:
    """
    Get pagination parameters dependency

    使用 Pydantic 模型自动验证和序列化分页参数

    Example:
        @app.get("/users")
        def get_users(pagination: PaginationParams = Depends(get_pagination)):
            offset = pagination.offset
            limit = pagination.pageSize

    Args:
        current: 当前页码，从1开始
        pageSize: 每页数量，1-100

    Returns:
        PaginationParams: 分页参数对象
    """
    return PaginationParams(current=current, pageSize=pageSize)


# =============================================================================
# Repository Dependencies
# =============================================================================


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Get user repository dependency

    Args:
        db: 数据库会话（自动注入）

    Returns:
        UserRepository: 用户仓储实例
    """
    return UserRepository(db)


# =============================================================================
# Service Dependencies
# =============================================================================


async def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    """
    Get user service dependency

    Args:
        repo: 用户仓储（自动注入）

    Returns:
        UserService: 用户服务实例
    """
    return UserService(repo=repo)


# =============================================================================
# Pattern Skill Dependencies
# =============================================================================


async def get_pattern_skill_repository(
    db: AsyncSession = Depends(get_db),
) -> PatternSkillRepository:
    return PatternSkillRepository(db)


async def get_pattern_skill_service(
    repo: PatternSkillRepository = Depends(get_pattern_skill_repository),
) -> PatternSkillService:
    return PatternSkillService(repo=repo)


# =============================================================================
# Authentication Dependencies
# =============================================================================


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_auth_service(repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    """
    Get auth service dependency
    """
    return AuthService(user_repo=repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme), service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Get current authenticated user
    """
    return await service.validate_access_token(token)


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user
    """
    if not current_user.is_active:
        from app.exceptions.base import UnauthorizedException

        raise UnauthorizedException("Inactive user")
    return current_user
