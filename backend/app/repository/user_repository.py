from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy import update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.base import utc_now
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """
    用户数据访问层 (异步版本)

    所有查询方法默认过滤已软删除的记录（deleted_at IS NULL）
    除非使用 include_deleted=True 参数
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_query(self, include_deleted: bool = False):
        """
        获取基础查询

        Args:
            include_deleted: 是否包含已删除记录

        Returns:
            SQLAlchemy Select 对象
        """
        query = select(User)
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))
        return query

    async def add(self, user: UserCreate) -> User:
        """创建用户"""
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=get_password_hash(user.password),
        )
        self.db.add(db_user)
        await self.db.flush()
        await self.db.refresh(db_user)
        return db_user

    async def find_by_id(self, user_id: int, include_deleted: bool = False) -> User | None:
        """
        根据 ID 获取用户

        Args:
            user_id: 用户 ID
            include_deleted: 是否包含已删除记录

        Returns:
            User 或 None
        """
        query = self._base_query(include_deleted).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str, include_deleted: bool = False) -> User | None:
        """
        根据邮箱 获取用户

        Args:
            email: 邮箱
            include_deleted: 是否包含已删除记录

        Returns:
            User 或 None
        """
        query = self._base_query(include_deleted).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_by_username(self, username: str, include_deleted: bool = False) -> User | None:
        """
        根据用户名获取用户

        Args:
            username: 用户名
            include_deleted: 是否包含已删除记录

        Returns:
            User 或 None
        """
        query = self._base_query(include_deleted).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_all(self, include_deleted: bool = False) -> list[User]:
        """
        获取所有用户

        Args:
            include_deleted: 是否包含已删除记录

        Returns:
            用户列表
        """
        query = self._base_query(include_deleted)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_paginated(
        self,
        current: int = 1,
        page_size: int = 10,
        include_deleted: bool = False,
        created_at_start: Optional[datetime] = None,
        created_at_end: Optional[datetime] = None,
        updated_at_start: Optional[datetime] = None,
        updated_at_end: Optional[datetime] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "id",
        sort_order: str = "desc",
    ) -> tuple[list[User], int]:
        """
        分页获取用户（支持过滤和排序）

        Args:
            current: 当前页码
            page_size: 每页数量
            include_deleted: 是否包含已删除记录
            created_at_start: 创建时间起始
            created_at_end: 创建时间结束
            updated_at_start: 更新时间起始
            updated_at_end: 更新时间结束
            username: 用户名搜索（模糊匹配）
            email: 邮箱搜索（模糊匹配）
            is_active: 是否激活
            sort_by: 排序字段（id, created_at, updated_at, username, email）
            sort_order: 排序方向（asc, desc）

        Returns:
            (用户列表, 总数)
        """
        offset = (current - 1) * page_size
        query = self._base_query(include_deleted)

        # Apply filters
        conditions = []

        if created_at_start:
            conditions.append(User.created_at >= created_at_start)
        if created_at_end:
            conditions.append(User.created_at <= created_at_end)
        if updated_at_start:
            conditions.append(User.updated_at >= updated_at_start)
        if updated_at_end:
            conditions.append(User.updated_at <= updated_at_end)
        if username:
            conditions.append(User.username.ilike(f"%{username}%"))
        if email:
            conditions.append(User.email.ilike(f"%{email}%"))
        if is_active is not None:
            conditions.append(User.is_active == is_active)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(User)
        if not include_deleted:
            count_query = count_query.where(User.deleted_at.is_(None))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply sorting
        sort_field_map = {
            "id": User.id,
            "created_at": User.created_at,
            "updated_at": User.updated_at,
            "username": User.username,
            "email": User.email,
        }
        sort_field = sort_field_map.get(sort_by, User.id)

        if sort_order.lower() == "asc":
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())

        # Get paginated data
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        users = list(result.scalars().all())

        return users, total

    async def update_by_id(self, user_id: int, user_update: UserUpdate) -> User | None:
        """
        更新用户

        Args:
            user_id: 用户 ID
            user_update: 更新数据

        Returns:
            更新后的 User 或 None
        """
        user = await self.find_by_id(user_id)
        if user:
            update_data = user_update.model_dump(exclude_unset=True)
            if "password" in update_data:
                update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            for key, value in update_data.items():
                setattr(user, key, value)
            await self.db.flush()
            await self.db.refresh(user)
        return user

    async def remove_by_id(self, user_id: int) -> bool:
        """
        软删除用户（优化版：使用 UPDATE 语句，避免先查询）

        Args:
            user_id: 用户 ID

        Returns:
            是否删除成功
        """
        stmt = (
            sql_update(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .values(deleted_at=utc_now())
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def hard_delete_by_id(self, user_id: int) -> bool:
        """
        物理删除用户（真正从数据库删除）

        Args:
            user_id: 用户 ID

        Returns:
            是否删除成功
        """
        user = await self.find_by_id(user_id, include_deleted=True)
        if user:
            await self.db.delete(user)
            await self.db.flush()
            return True
        return False

    async def restore_by_id(self, user_id: int) -> User | None:
        """
        恢复已软删除的用户（优化版：使用 UPDATE 后查询一次）

        Args:
            user_id: 用户 ID

        Returns:
            恢复后的 User 或 None
        """
        stmt = (
            sql_update(User)
            .where(User.id == user_id, User.deleted_at.is_not(None))
            .values(deleted_at=None)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()

        if result.rowcount > 0:
            # 恢复成功，查询返回用户对象
            return await self.find_by_id(user_id)
        return None

    async def find_deleted(self, current: int = 1, page_size: int = 10) -> tuple[list[User], int]:
        """
        分页获取已删除的用户

        Args:
            current: 当前页码
            page_size: 每页数量

        Returns:
            (用户列表, 总数)
        """
        offset = (current - 1) * page_size
        query = select(User).where(User.deleted_at.is_not(None))

        # 获取总数
        count_query = select(func.count()).select_from(User).where(User.deleted_at.is_not(None))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # 获取分页数据
        query = query.order_by(User.deleted_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        users = list(result.scalars().all())

        return users, total
