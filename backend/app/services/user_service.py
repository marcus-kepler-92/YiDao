"""
User Service

Business logic layer for user operations with fastapi-cache2 integration.
"""

import logging
from typing import TYPE_CHECKING

from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.constants import Messages
from app.exceptions import ConflictException, NotFoundException
from app.models.user import User
from app.repository.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate

if TYPE_CHECKING:
    from app.schemas.user import UserListQueryParams

logger = logging.getLogger(__name__)


class UserService:
    """
    User business logic layer

    Responsibilities:
        - Business logic processing
        - Data validation
        - Cache management (using fastapi-cache2)
        - Cross-repository operation coordination
    """

    def __init__(self, repo: UserRepository):
        """
        Initialize UserService

        Args:
            repo: User repository instance
        """
        self.repo = repo

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create user

        Args:
            user_data: User creation data

        Returns:
            Created user

        Raises:
            ConflictException: Email or username already exists
        """
        # Business validation: check email uniqueness
        if await self.repo.find_by_email(user_data.email):
            raise ConflictException(message=Messages.EMAIL_EXISTS)

        # Business validation: check username uniqueness
        if await self.repo.find_by_username(user_data.username):
            raise ConflictException(message=Messages.USERNAME_EXISTS)

        # Create user
        user = await self.repo.add(user_data)
        logger.info(f"User created: {user.id}")

        # Clear list cache
        await FastAPICache.clear(namespace="user_list")

        return user

    @cache(expire=300)  # Cache for 5 minutes, key auto-generated: UserService.get_user:user_id=1
    async def get_user(self, user_id: int) -> UserResponse:
        """
        Get user details

        Decorator automatically handles caching:
        - Auto-generates key: "UserService.get_user:user_id=1"
        - Auto serializes/deserializes
        - Auto expiration management

        Args:
            user_id: User ID

        Returns:
            User response object (Pydantic model)

        Raises:
            NotFoundException: User not found
        """
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise NotFoundException(message=Messages.USER_NOT_FOUND)

        return UserResponse.model_validate(user)

    async def get_user_list(
        self,
        current: int = 1,
        pageSize: int = 10,
        query_params: "UserListQueryParams | None" = None,
    ) -> tuple[list[UserResponse], int]:
        """
        Get user list (paginated)

        Args:
            current: Current page number
            pageSize: Items per page
            query_params: Optional query parameters for filtering and sorting

        Returns:
            (User response list, total count)
        """
        from app.schemas.user import UserListQueryParams

        if query_params is None:
            query_params = UserListQueryParams()

        users, total = await self.repo.find_paginated(
            current=current,
            page_size=pageSize,
            created_at_start=query_params.created_at_start,
            created_at_end=query_params.created_at_end,
            updated_at_start=query_params.updated_at_start,
            updated_at_end=query_params.updated_at_end,
            username=query_params.username,
            email=query_params.email,
            is_active=query_params.is_active,
            sort_by=query_params.sort_by,
            sort_order=query_params.sort_order,
        )
        user_responses = [UserResponse.model_validate(u) for u in users]
        return user_responses, total

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """
        Update user

        Args:
            user_id: User ID
            user_data: Update data

        Returns:
            Updated user

        Raises:
            NotFoundException: User not found
            ConflictException: Email or username conflict
        """
        # Check if user exists
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise NotFoundException(message=Messages.USER_NOT_FOUND)

        # Check email uniqueness
        if user_data.email and user_data.email != user.email:
            if await self.repo.find_by_email(user_data.email):
                raise ConflictException(message=Messages.EMAIL_EXISTS)

        # Check username uniqueness
        if user_data.username and user_data.username != user.username:
            if await self.repo.find_by_username(user_data.username):
                raise ConflictException(message=Messages.USERNAME_EXISTS)

        # Update user
        updated_user = await self.repo.update_by_id(user_id, user_data)
        logger.info(f"User updated: {user_id}")

        # Clear cache
        await FastAPICache.clear(namespace="", key=f"UserService.get_user:user_id={user_id}")
        await FastAPICache.clear(namespace="user_list")

        return updated_user

    async def delete_user(self, user_id: int) -> bool:
        """
        Delete user (soft delete)

        Args:
            user_id: User ID

        Returns:
            Whether deletion succeeded

        Raises:
            NotFoundException: User not found
        """
        if not await self.repo.remove_by_id(user_id):
            raise NotFoundException(message=Messages.USER_NOT_FOUND)

        logger.info(f"User soft deleted: {user_id}")

        # Clear cache
        await FastAPICache.clear(namespace="", key=f"UserService.get_user:user_id={user_id}")
        await FastAPICache.clear(namespace="user_list")

        return True

    async def restore_user(self, user_id: int) -> User:
        """
        Restore deleted user

        Args:
            user_id: User ID

        Returns:
            Restored user

        Raises:
            NotFoundException: User not found or not deleted
        """
        user = await self.repo.restore_by_id(user_id)
        if not user:
            raise NotFoundException(message=Messages.USER_NOT_FOUND)

        logger.info(f"User restored: {user_id}")

        # Clear cache
        await FastAPICache.clear(namespace="", key=f"UserService.get_user:user_id={user_id}")
        await FastAPICache.clear(namespace="user_list")

        return user

    async def get_deleted_users(
        self, current: int = 1, pageSize: int = 10
    ) -> tuple[list[UserResponse], int]:
        """
        Get deleted user list

        Args:
            current: Current page number
            pageSize: Items per page

        Returns:
            (User response list, total count)
        """
        # Deleted users are not cached, fetch directly from database
        users, total = await self.repo.find_deleted(current, pageSize)
        user_responses = [UserResponse.model_validate(user) for user in users]
        return user_responses, total
