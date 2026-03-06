from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import declared_attr

from app.core.database import Base


def utc_now() -> datetime:
    """获取当前 UTC 时间（timezone-aware）"""
    return datetime.now(timezone.utc)


class BaseModel(Base):
    """
    基础模型类，包含所有模型的公共字段

    字段:
        id: 主键
        created_at: 创建时间（UTC，timezone-aware）
        updated_at: 更新时间（UTC，自动更新）
        deleted_at: 删除时间（软删除标记）
    """

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    @property
    def is_deleted(self) -> bool:
        """检查记录是否已被软删除"""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """软删除当前记录"""
        self.deleted_at = utc_now()

    def restore(self) -> None:
        """恢复软删除的记录"""
        self.deleted_at = None

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name with simple English pluralization rules."""
        name = cls.__name__.lower()
        # Handle common irregular plurals
        if name.endswith(("s", "x", "z", "ch", "sh")):
            return name + "es"
        elif name.endswith("y") and len(name) > 1 and name[-2] not in "aeiou":
            return name[:-1] + "ies"
        return name + "s"
