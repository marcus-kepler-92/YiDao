# 企业级测试策略

## 📊 测试金字塔

```
        /\
       /E2E\          ← 端到端测试 (10%)
      /------\
     /Integration\   ← 集成测试 (20%)
    /------------\
   /   Unit Tests  \  ← 单元测试 (70%)
  /----------------\
```

### 测试分布比例

| 测试类型 | 比例 | 数量 | 执行速度 | 维护成本 |
|---------|------|------|---------|---------|
| **单元测试** | 70% | ~100+ | 毫秒级 | 低 |
| **集成测试** | 20% | ~30 | 秒级 | 中 |
| **端到端测试** | 10% | ~10 | 分钟级 | 高 |

---

## 🎯 测试覆盖率目标

### 代码覆盖率

| 层级 | 覆盖率目标 | 当前状态 |
|------|-----------|---------|
| **Service 层** | ≥ 90% | ✅ 95%+ |
| **Repository 层** | ≥ 85% | ⚠️ 待补充 |
| **API 层** | ≥ 80% | ✅ 85%+ |
| **工具函数** | ≥ 95% | ✅ 100% |
| **整体项目** | ≥ 85% | ⚠️ 75% |

### 分支覆盖率

- **关键业务逻辑**: ≥ 95%
- **错误处理路径**: ≥ 90%
- **边界条件**: ≥ 85%

---

## 📁 测试目录结构

```
tests/
├── unit/                    # 单元测试 (70%)
│   ├── services/            # Service 层测试
│   │   ├── test_user_service.py
│   │   └── test_product_service.py
│   ├── repository/          # Repository 层测试
│   │   ├── test_user_repository.py
│   │   └── test_product_repository.py
│   ├── utils/               # 工具函数测试
│   │   └── test_cache_helper.py
│   └── core/                # 核心功能测试
│       ├── test_config.py
│       └── test_database.py
│
├── integration/             # 集成测试 (20%)
│   ├── api/                 # API 集成测试
│   │   ├── test_users.py
│   │   └── test_products.py
│   ├── database/            # 数据库集成测试
│   │   └── test_migrations.py
│   └── cache/               # 缓存集成测试
│       └── test_redis_cache.py
│
├── e2e/                     # 端到端测试 (10%)
│   ├── test_user_workflow.py
│   └── test_api_contract.py
│
├── performance/             # 性能测试
│   ├── test_load.py
│   └── test_stress.py
│
├── security/                # 安全测试
│   ├── test_authentication.py
│   └── test_authorization.py
│
├── fixtures/                 # 测试数据
│   ├── users.json
│   └── products.json
│
├── conftest.py              # 全局 fixtures
└── README.md                # 测试文档
```

---

## 🧪 测试类型详解

### 1. 单元测试 (Unit Tests)

**目标**: 测试单个函数/方法的业务逻辑

**特点**:
- ✅ 快速执行（< 100ms）
- ✅ 完全隔离（使用 Mock）
- ✅ 覆盖所有分支
- ✅ 测试边界条件

**示例**:
```python
# tests/unit/services/test_user_service.py
class TestUserServiceCreate:
    @pytest.mark.asyncio
    async def test_create_user_success(...):
        """测试正常创建用户"""
    
    @pytest.mark.asyncio
    async def test_create_user_email_exists(...):
        """测试邮箱冲突"""
    
    @pytest.mark.asyncio
    async def test_create_user_username_exists(...):
        """测试用户名冲突"""
```

**覆盖率要求**: ≥ 90%

---

### 2. 集成测试 (Integration Tests)

**目标**: 测试多个组件协作

**类型**:

#### 2.1 API 集成测试
- 测试完整的 HTTP 请求-响应流程
- 验证路由、序列化、验证
- 测试中间件（限流、认证等）

```python
# tests/integration/api/test_users.py
class TestUserAPI:
    def test_create_user_endpoint(...):
        """测试 POST /api/v1/users"""
    
    def test_get_user_list_with_filters(...):
        """测试查询参数功能"""
```

#### 2.2 数据库集成测试
- 使用测试数据库
- 测试 Repository 层与数据库交互
- 测试事务、约束、索引

```python
# tests/integration/database/test_user_repository.py
@pytest.mark.asyncio
async def test_find_paginated_with_filters(db_session):
    """测试分页查询与数据库交互"""
```

#### 2.3 缓存集成测试
- 测试 Redis 缓存功能
- 测试缓存失效逻辑
- 测试缓存一致性

**覆盖率要求**: ≥ 80%

---

### 3. 端到端测试 (E2E Tests)

**目标**: 测试完整的用户场景

**特点**:
- 使用真实数据库（测试环境）
- 测试完整业务流程
- 验证 API 契约

```python
# tests/e2e/test_user_workflow.py
class TestUserWorkflow:
    def test_user_lifecycle(self, client, db):
        """测试用户完整生命周期"""
        # 1. 创建用户
        # 2. 查询用户
        # 3. 更新用户
        # 4. 删除用户
        # 5. 恢复用户
```

**覆盖率要求**: 关键业务流程 100%

---

### 4. 性能测试 (Performance Tests)

**目标**: 验证系统性能指标

**类型**:
- **负载测试**: 正常负载下的性能
- **压力测试**: 极限负载下的表现
- **容量测试**: 系统容量上限

```python
# tests/performance/test_load.py
@pytest.mark.performance
def test_user_list_performance(client):
    """测试用户列表查询性能"""
    import time
    start = time.time()
    response = client.get("/api/v1/users")
    duration = time.time() - start
    
    assert response.status_code == 200
    assert duration < 0.5  # 500ms 内响应
```

**性能指标**:
- API 响应时间: P95 < 500ms
- 数据库查询: < 100ms
- 缓存命中率: > 80%

---

### 5. 安全测试 (Security Tests)

**目标**: 验证安全机制

**测试内容**:
- 认证/授权
- SQL 注入防护
- XSS 防护
- 速率限制
- 输入验证

```python
# tests/security/test_authentication.py
class TestSecurity:
    def test_sql_injection_protection(client):
        """测试 SQL 注入防护"""
        response = client.get(
            "/api/v1/users",
            params={"username": "admin' OR '1'='1"}
        )
        # 应该安全处理，不返回所有用户
```

---

## 🏷️ 测试标记 (Markers)

```python
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (slower, with dependencies)",
    "e2e: End-to-end tests (slowest, full stack)",
    "performance: Performance tests",
    "security: Security tests",
    "slow: Slow running tests",
    "database: Tests requiring database",
    "redis: Tests requiring Redis",
]
```

**使用示例**:
```python
@pytest.mark.unit
async def test_user_service(...):
    """单元测试"""

@pytest.mark.integration
@pytest.mark.database
def test_user_api(...):
    """集成测试，需要数据库"""

@pytest.mark.e2e
@pytest.mark.slow
def test_user_workflow(...):
    """端到端测试，较慢"""
```

---

## 📊 测试覆盖率配置

### pytest-cov 配置

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = [
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=85",  # 覆盖率低于 85% 时失败
    "--cov-branch",          # 分支覆盖率
]
```

### 覆盖率报告

```bash
# 生成 HTML 报告
pytest --cov=app --cov-report=html
# 打开 htmlcov/index.html 查看

# 生成 XML 报告（用于 CI）
pytest --cov=app --cov-report=xml
```

---

## 🔄 CI/CD 集成

### GitHub Actions 示例

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=app --cov-report=xml
      
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: |
          pytest tests/integration/ -v
  
  coverage:
    needs: [unit-tests]
    runs-on: ubuntu-latest
    steps:
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📈 测试指标和监控

### 关键指标

1. **测试覆盖率**
   - 代码覆盖率: ≥ 85%
   - 分支覆盖率: ≥ 80%

2. **测试执行时间**
   - 单元测试: < 30 秒
   - 集成测试: < 5 分钟
   - 端到端测试: < 15 分钟

3. **测试通过率**
   - 目标: 100%
   - 允许: ≥ 95%（临时）

4. **测试稳定性**
   - 失败重试率: < 5%
   - Flaky 测试: 0 个

---

## 🎯 当前项目测试规划

### 已完成 ✅

- [x] 单元测试框架搭建
- [x] Service 层单元测试（30+ 测试用例）
- [x] API 集成测试基础框架
- [x] Mock fixtures 配置
- [x] 测试标记系统

### 待补充 ⚠️

- [ ] Repository 层单元测试
- [ ] 数据库集成测试
- [ ] 缓存集成测试
- [ ] 端到端测试
- [ ] 性能测试
- [ ] 安全测试
- [ ] CI/CD 集成
- [ ] 测试覆盖率报告

---

## 📝 测试最佳实践

### 1. 测试命名规范

```python
# ✅ 好的命名
def test_create_user_with_valid_data_should_succeed(...)
def test_create_user_with_duplicate_email_should_fail(...)

# ❌ 不好的命名
def test_user(...)
def test1(...)
```

### 2. 测试结构 (AAA 模式)

```python
def test_example():
    # Arrange - 准备测试数据
    user_data = UserCreate(...)
    
    # Act - 执行操作
    result = await service.create_user(user_data)
    
    # Assert - 验证结果
    assert result.id is not None
    assert result.email == user_data.email
```

### 3. 测试隔离

- 每个测试独立运行
- 不依赖其他测试的执行顺序
- 使用 fixtures 管理测试数据

### 4. 测试数据管理

```python
# tests/fixtures/users.json
{
  "valid_user": {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }
}
```

---

## 🚀 下一步行动

1. **补充 Repository 层测试** (优先级: 高)
2. **添加数据库集成测试** (优先级: 高)
3. **配置 CI/CD 测试流程** (优先级: 中)
4. **添加性能测试** (优先级: 中)
5. **添加安全测试** (优先级: 低)

---

## 📚 参考资源

- [pytest 官方文档](https://docs.pytest.org/)
- [FastAPI 测试指南](https://fastapi.tiangolo.com/tutorial/testing/)
- [测试金字塔理论](https://martinfowler.com/articles/practical-test-pyramid.html)
