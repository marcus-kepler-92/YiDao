# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 常用命令

### 依赖管理
```bash
# 安装所有依赖
uv sync

# 安装开发依赖
uv sync --extra dev

# 安装新依赖
uv add <package-name>
# 注意: 开发依赖配置在 pyproject.toml 的 [project.optional-dependencies] 中
# 因此安装时需要使用 --extra 标志, 而不是 --dev (后者用于 dependency-groups)
```

### 本地开发
```bash
# 方式 1: 直接运行 (需要本地 PostgreSQL 和 Redis)
# ⚠️ 注意: 确保 .env 中 DB_HOST=localhost
uv run python main.py

# 方式 2: 使用 Docker Compose 启动基础设施
# 启动数据库和 Redis 容器 (映射端口到本地)
docker-compose up -d db redis
# ⚠️ 注意: 确保 .env 中 DB_HOST=localhost
uv run python main.py

# 方式 3: 完整 Docker 开发环境
.\scripts\docker-dev.ps1
```

### 数据库迁移
```bash
# 创建迁移文件
uv run alembic revision --autogenerate -m "description"

# 执行迁移
uv run alembic upgrade head

# 回滚迁移
uv run alembic downgrade -1
```

### 测试
```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/api/test_users.py

# 运行特定测试函数
uv run pytest tests/api/test_users.py::test_add_user

# 运行带覆盖率报告
uv run pytest --cov=app --cov-report=html

# 运行特定标记的测试
uv run pytest -m unit        # 单元测试
uv run pytest -m api         # API 集成测试
```

### 代码质量
```bash
# 格式化代码
uv run black app tests

# 代码检查
uv run ruff check app tests

# 类型检查
uv run mypy app
```

### Docker 操作 (PowerShell)
```powershell
# 开发环境
.\scripts\docker-dev.ps1

# QA 环境
.\scripts\docker-qa.ps1

# 生产环境
.\scripts\docker-prod.ps1

# 查看日志
.\scripts\docker-logs.ps1

# 查看状态
.\scripts\docker-status.ps1

# 重启服务
.\scripts\docker-restart.ps1

# 停止所有服务
.\scripts\docker-down.ps1

# 清理容器和卷
.\scripts\docker-clean.ps1
```

## 架构设计

### 分层架构
项目采用经典的分层架构设计,遵循单一职责原则:

```
API Layer (app/api/)
    ↓
Service Layer (app/services/)
    ↓
Repository Layer (app/repository/)
    ↓
Model Layer (app/models/)
```

**关键点:**
- **API 层**: 仅负责请求解析、参数验证、响应格式化,不包含业务逻辑
- **Service 层**: 包含所有业务逻辑,协调 Repository 和外部服务 (如 Cache)
- **Repository 层**: 封装数据库操作,提供类型安全的 CRUD 接口
- **Model 层**: SQLAlchemy ORM 模型,定义数据库表结构

### 异步架构 ⚡
**重要:** 本项目采用全异步架构,从数据库到 API 层全部使用 async/await:

- **数据库驱动**: 使用 `asyncpg` (PostgreSQL 异步驱动)
- **SQLAlchemy**: 使用 `AsyncEngine` 和 `AsyncSession`
- **Repository 层**: 所有方法都是 `async def`
- **Service 层**: 所有方法都是 `async def`
- **API 层**: 所有路由处理器都是 `async def`

**重要规则:**
1. 所有数据库操作必须使用 `await`
2. 查询必须使用 `select()` 而不是 `query()`
3. 执行查询: `result = await db.execute(query)`
4. 获取结果: `result.scalar_one_or_none()` / `result.scalars().all()`
5. 事务提交: `await db.flush()` / `await db.commit()` (由依赖注入自动处理)

### 身份验证系统 🔐
项目实现了基于 JWT 的生产级身份验证系统:

- **JWT 策略**: 使用 Access Token (30m) 和 Refresh Token (30d)。
- **令牌轮换**: 刷新令牌在使用后失效并签发新对,防止被盗用。
- **撤销机制**: 使用 Redis 存储黑名单,支持安全的登出和令牌撤销。
- **密码安全**: 使用 `passlib[bcrypt]` 进行哈希存储。

**身份验证依赖**:
- `get_current_user`: 验证并返回当前用户对象。
- `get_current_active_user`: 验证并确保用户处于激活状态。

---

### 依赖注入系统
所有依赖通过 `app/dependencies.py` 集中管理 (全部为异步):

```python
# 数据库会话 (异步)
db: AsyncSession = Depends(get_db)

# 身份验证 (获取当前用户)
current_user: User = Depends(get_current_active_user)

# 身份验证服务
auth_service: AuthService = Depends(get_auth_service)
```

**测试时覆盖依赖**:
```python
# 异步依赖需要使用 async lambda 或 async def
async def mock_repo_override():
    return mock_repo

app.dependency_overrides[get_user_repository] = mock_repo_override
```

### 统一响应格式
所有 API 响应使用 `app/schemas/common.py` 中定义的统一格式:

- **标准响应**: `Response[T]` - 包含 `success`, `message`, `data`
- **分页响应**: `PaginatedResponse[T]` - 额外包含 `current`, `pageSize`, `total`

路由处理器应该返回原始数据对象,中间件会自动包装成统一格式。

### 中间件执行顺序
中间件在 `app/middlewares/__init__.py:setup_middlewares()` 中按特定顺序注册 (执行顺序与注册顺序相反):

1. **CORS** - 处理跨域请求 (最外层)
2. **Rate Limiting** - 限流保护
3. **Tracing** - 链路追踪,添加 `X-Trace-ID` 到响应
4. **Prometheus Metrics** - 收集指标 (请求计数、延迟等)
5. **Audit** - 审计日志,记录所有请求到 `audit_log` 表

### 异常处理
自定义异常定义在 `app/exceptions/`:
- 所有业务异常继承自 `AppException`
- 异常处理器在 `app/exceptions/handlers.py:setup_exception_handlers()` 中统一注册
- 异常会自动转换为统一的响应格式

### 配置管理
配置通过 `app/core/config.py` 的 `Settings` 类管理:
- 使用 Pydantic Settings 自动读取环境变量
- 支持 `.env` 文件 (开发环境) 和系统环境变量 (生产环境)
- 提供智能默认值和验证器 (例如自动拼接 `database_url`)

**Redis 数据库分配**:
- DB 0: 缓存
- DB 1: Session
- DB 2: Celery Broker
- DB 3: Celery Backend
- DB 4: Rate Limiting

### 日志和监控
- **日志**: 结构化日志通过 `app/core/logger.py` 配置,支持 JSON 格式
- **追踪**: OpenTelemetry 集成在 `app/core/tracing.py`
  - 自动追踪 HTTP 请求 (FastAPI)
  - 自动追踪数据库查询 (SQLAlchemy - 异步和同步)
  - 自动追踪 Redis 操作
  - 自动追踪 Celery 任务执行
  - 支持导出到 Jaeger/OTLP (生产环境)
  - Trace Context 自动传播到 Celery 任务
- **指标**: Prometheus 指标通过 `/metrics` 端点暴露
  - HTTP 请求计数和延迟
  - Celery 任务成功/失败计数
  - 用户统计指标 (活跃/非活跃/已删除)
- **审计**: 所有 API 请求通过 Celery 异步任务记录到 `audit_log` 表

### 命名约定
严格遵循 README.md 中定义的命名规范:

**Repository 方法**:
- `add()` - 创建
- `find_by_id()` - 按 ID 查询
- `find_by_*()` - 按字段查询
- `find_all()` / `find_paginated()` - 列表查询
- `update_by_id()` - 更新
- `remove_by_id()` - 软删除

**API 路由函数**:
- `add_*()` - POST 创建
- `get_*_detail()` - GET 单个
- `get_*_list()` - GET 列表
- `update_*_by_id()` - PUT 更新
- `remove_*_by_id()` - DELETE 删除

## 重要实现细节

### 软删除实现
模型继承 `app/models/base.py:SoftDeleteMixin`,提供:
- `deleted_at` 字段
- `is_deleted` 计算属性
- Repository 层自动过滤已删除记录

### 缓存策略
项目使用 `fastapi-cache2` 进行缓存，配合 Redis 后端：

**Service 层使用方式：**
```python
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

class UserService:
    # 1. 使用装饰器自动缓存查询结果
    @cache(expire=300, namespace="user")
    async def get_user(self, user_id: int) -> UserResponse:
        user = await self.repo.find_by_id(user_id)
        return UserResponse.model_validate(user)

    # 2. 更新后清除缓存
    async def update_user(self, user_id: int, data: UserUpdate):
        user = await self.repo.update(user_id, data)
        # 清除单个用户缓存
        await FastAPICache.clear(namespace="user", key=f"get_user:user_id={user_id}")
        return UserResponse.model_validate(user)
```

**缓存键规范：**
- namespace + method name + params 自动生成
- 示例: `user:get_user:user_id=123`

**最佳实践：**
- ✅ 查询方法使用 `@cache` 装饰器
- ✅ 缓存 Pydantic 响应模型，不缓存 ORM 对象
- ✅ 写操作后用 `FastAPICache.clear()` 清除相关缓存
- ✅ 使用 `namespace` 参数组织缓存键

### API 版本管理
- API 路由通过 `app/api/router.py:register_routers()` 集中注册
- V1 路由挂载在 `/api/v1` 前缀下
- 每个版本的路由在独立子包中 (`app/api/v1/`)

### 测试架构
`tests/conftest.py` 提供完整的测试 fixtures:
- **Mock 对象**: `mock_db_session`, `mock_cache`, `mock_user_repository` (使用 `AsyncMock`)
- **测试客户端**: `client` (完整集成), `client_with_mocked_service` (依赖隔离)
- **Sample 数据**: `sample_user`, `sample_users`, `sample_user_data`

测试时自动禁用限流 (`ENABLE_RATE_LIMIT=false`),所有外部依赖 (DB, Redis, Tracing) 都被 mock。

### Celery 异步任务
`app/tasks.py` 提供 Celery 任务定义和配置:

**架构统一 ✅:**
- Celery 任务通过 `run_async()` 包装器运行异步代码
- 与 FastAPI 使用相同的异步数据库访问 (`AsyncEngine` + `AsyncSession`)
- 复用 Service 和 Repository 层，避免维护两套代码

**数据库访问:**
```python
@app.task
def my_celery_task():
    # ✅ 使用 run_async() 运行异步代码
    return run_async(async_my_task())

async def async_my_task():
    # ✅ 使用异步数据库上下文
    async with get_async_db_context() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        # 自动 commit
```

**已实现的任务:**
- `record_audit_log_task` - 异步记录审计日志 (支持 trace 传播)
- `update_user_metrics_task` - 每小时更新用户统计指标到 Prometheus
- `daily_report_task` - 每日报告 (示例)
- `send_email_task` - 发送邮件 (示例)

**Celery 命令:**
```bash
# 启动 worker
celery -A app.tasks worker --loglevel=info

# 启动 beat (定时任务调度器)
celery -A app.tasks beat --loglevel=info

# 同时启动 worker 和 beat
celery -A app.tasks worker --beat --loglevel=info
```

**OpenTelemetry 集成:**
- Celery 任务自动被追踪 (通过 `CeleryInstrumentor`)
- Trace context 自动从 API 请求传播到 Celery 任务
- 可在 Jaeger 中查看完整的请求链路：API → Celery Task → Database

## 编写新功能示例

### 添加新的 Repository 方法
```python
# app/repository/user_repository.py
async def find_by_status(self, status: str) -> list[User]:
    """按状态查询用户"""
    query = select(User).where(User.status == status, User.deleted_at.is_(None))
    result = await self.db.execute(query)
    return list(result.scalars().all())
```

### 添加新的 Service 方法
```python
# app/services/user_service.py
async def get_active_users(self) -> list[User]:
    """获取所有活跃用户"""
    users = await self.repo.find_by_status("active")
    return users
```

### 添加新的 API 端点
```python
# app/api/v1/users.py
@router.get("/active", response_model=Response[list[UserResponse]])
async def get_active_users(service: UserService = Depends(get_user_service)):
    """获取活跃用户列表"""
    users = await service.get_active_users()
    return Response(data=users)
```

**关键点:** 注意每一层都使用 `async def` 和 `await`,保持整个调用链的异步性。

## 性能优化要点

### 1. 数据库查询优化
- ✅ **使用 UPDATE 语句代替先查询后更新**: `remove_by_id` 和 `restore_by_id` 使用直接 UPDATE，减少数据库往返
- ✅ **连接池配置**: 配置了 `pool_timeout`、`pool_recycle`、`command_timeout` 等参数
- ✅ **应用名称标识**: 通过 `application_name` 方便数据库监控和问题排查

```python
# ❌ 低效：先查询后更新
user = await repo.find_by_id(user_id)
if user:
    user.deleted_at = utc_now()
    await db.flush()

# ✅ 高效：直接 UPDATE
stmt = update(User).where(User.id == user_id).values(deleted_at=utc_now())
result = await db.execute(stmt)
```

### 2. 时区处理
- ✅ 使用 `datetime.now(timezone.utc)` 替代已废弃的 `datetime.utcnow()`
- ✅ 数据库字段使用 `DateTime(timezone=True)` 存储 timezone-aware datetime
- ✅ 统一使用 `utc_now()` 辅助函数

### 3. 依赖注入优化
- ✅ 顶部导入代替运行时导入，提升性能和类型检查
- ✅ 明确类型注解，IDE 能提供更好的代码提示

### 4. 缓存优化
- ✅ 缓存命中时直接返回，避免无意义的数据库查询
- ✅ 列表缓存包含完整数据，不只是元数据
- ⚠️ 注意缓存失效策略，写操作后及时清除
