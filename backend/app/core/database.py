import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# 声明基类
# ============================================================================

Base = declarative_base()

# ============================================================================
# 数据库引擎配置
# ============================================================================

# 将 postgresql:// 转换为 postgresql+asyncpg://
async_database_url = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
).replace("postgresql+psycopg://", "postgresql+asyncpg://")

engine: AsyncEngine = create_async_engine(
    async_database_url,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # 使用前检查连接有效性
    pool_recycle=3600,  # 1小时回收一次连接
    pool_timeout=30,  # 获取连接超时时间（秒）
    echo=settings.debug,  # 开发模式下输出 SQL
    echo_pool=settings.debug,  # 开发模式下输出连接池日志
    connect_args={
        "server_settings": {
            "application_name": settings.app_name,  # 数据库中显示的应用名称
            "jit": "off",  # 禁用 JIT 编译（可选，某些查询下提升性能）
        },
        "command_timeout": 60,  # 单个查询超时时间（秒）
        "timeout": 10,  # 连接超时时间（秒）
    },
)

# ============================================================================
# Session 工厂 (异步)
# ============================================================================

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ============================================================================
# Celery 任务现在通过 asyncio.run() 使用异步数据库访问
# 这样可以复用 FastAPI 的异步 Repository 和 Service 层，保持架构统一
# ============================================================================

# ============================================================================
# 事件监听

# ============================================================================


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数 (异步版本)

    用途：
        在 FastAPI 路由中通过 Depends() 注入数据库 session

    示例：
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()

    Yields:
        AsyncSession: SQLAlchemy 异步数据库会话对象

    Raises:
        Exception: 数据库操作异常时回滚并抛出

    注意：
        事务由 Repository/Service 层控制，这里只负责会话管理
        如果出现异常会自动回滚，正常结束会自动提交挂起的更改
    """
    async with SessionLocal() as session:
        try:
            yield session
            # 只有在有待提交的更改时才提交
            # Repository 层使用 flush() 将更改发送到数据库
            # 这里的 commit() 会在请求结束时自动调用
            await session.commit()
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            await session.rollback()
            raise


# ============================================================================
# 初始化和清理函数
# ============================================================================


async def init_db() -> None:
    """
    初始化数据库 (异步版本)

    用途：
        - 开发环境：自动创建所有表（方便快速开发）
        - 生产环境：仅导入模型，不自动建表（使用 Alembic 迁移）

    注意：
        必须在应用启动前导入所有 models，保证 Base.metadata 里有表定义
    """
    # 导入所有 models，保证它们都注册到 Base.metadata
    from app import models  # noqa: F401

    # 仅在开发环境自动创建表，生产环境应使用 alembic upgrade head
    if settings.app_env == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables auto-created (development mode)")
    else:
        logger.info("Database models loaded (use 'alembic upgrade head' for migrations)")


async def close_db() -> None:
    """
    关闭数据库连接 (异步版本)

    用途：
        应用关闭时调用此函数以释放所有数据库连接
    """
    await engine.dispose()
    logger.info("Database connections closed")
