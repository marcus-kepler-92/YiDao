# YiDao 怎么跑

## 前置条件

- **后端**：Python 3.12+，[uv](https://docs.astral.sh/uv/)，PostgreSQL 16，Redis
- **前端**：Node.js 18+，npm

## 一、后端

### 1. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env：至少填 DB_*、REDIS_*、JWT_SECRET_KEY
```

**本机跑后端时（不用 Docker 跑 web）**，`.env` 里必须写成连本机上的数据库和 Redis：

- `DB_HOST=localhost`，`DB_PORT=5432`
- `DB_USER=postgres`，`DB_PASSWORD=postgres`，`DB_NAME=fastapi-template-db`（若你用 Docker 起 db，这三个要和**第一次**起 db 时一致）
- `REDIS_HOST=localhost`，`REDIS_PORT=6380`（compose 里 Redis 映射的是 **6380:6379**，本机连要用 6380）

### 2. 安装依赖

```bash
cd backend
uv sync --extra dev
```

### 3. 启动数据库、缓存与 Celery（二选一）

**方式 A：本机已装 PostgreSQL / Redis**

- 确保服务已启动，`.env` 里 `DB_HOST=localhost`、`REDIS_HOST=localhost`。Celery 需本机另起 worker/beat。

**方式 B：用 Docker 只起数据库、Redis、Celery（本机跑 web 时用）**

```bash
cd backend
docker compose up -d db redis celery_worker celery_beat
```

- 会启动：PostgreSQL（db）、Redis（redis）、Celery Worker、Celery Beat；**不启动** web，本机用 `uv run python main.py` 或 F5 调试。
- `.env` 里：`DB_HOST=localhost`，`REDIS_HOST=localhost`，**`REDIS_PORT=6380`**（compose 里 Redis 映射 6380:6379）。

### 4. 数据库迁移

```bash
cd backend
uv run alembic upgrade head
```

### 5. 启动后端

```bash
cd backend
uv run python main.py
```

- API：<http://localhost:9000>
- 文档：<http://localhost:9000/docs>

### 6. 访问不了 9000 时排查

1. **本机跑时：数据库和 Redis 的 .env 要对**  
   - 用 Docker 只起 db/redis 时：`DB_HOST=localhost`，`REDIS_HOST=localhost`，**`REDIS_PORT=6380`**（compose 里映射的是 6380）。  
   - 若出现 `password authentication failed for user "postgres"`：说明当前 `.env` 的 `DB_PASSWORD` 和 Postgres 里**实际密码**不一致（Postgres 是第一次起 db 容器时按当时 .env 初始化的）。  
   - **一次性修法**：删掉数据卷，用当前 .env 重新初始化：  
     `cd backend` → 确认 `.env` 里 `DB_USER=postgres`、`DB_PASSWORD=postgres`、`DB_NAME=fastapi-template-db` → 执行 `docker compose down -v` → `docker compose up -d db redis` → `uv run alembic upgrade head` → 再 `uv run python main.py`。

2. **看启动报错**  
   在 `backend` 下执行 `uv run python main.py`，若**连不上数据库**会直接报错退出，服务不会监听 9000。终端里看到 `Failed to initialize database` 或 `password authentication failed` 就是数据库配置/连接问题。

3. **确认端口**  
   服务正常时终端会打印 `Application is ready` 和 `API Docs: http://0.0.0.0:9000/docs`。再在终端执行：`lsof -i :9000`（Mac/Linux）或 `netstat -ano | findstr 9000`（Windows），应有进程在监听 9000。

4. **用 Docker 跑整套时**  
   `docker compose up -d` 后访问 <http://localhost:9000/docs>。若不行：`docker compose ps` 看 web 是否 Up；`docker compose logs web` 看是否有启动报错。

---

## 二、前端

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 开发环境运行

```bash
cd frontend
npm run dev
```

- 页面：<http://localhost:3000>
- 请求会通过 Vite 代理到后端 `http://localhost:9000`，无需单独配 CORS。开发时 `VITE_API_BASE` 留空即可；生产构建部署需在构建前配置 `VITE_API_BASE` 为后端地址。

### 3. 生产构建

```bash
cd frontend
npm run build
npm run preview   # 本地预览 dist
```

### 4. API 客户端根据 OpenAPI 自动生成（Orval）

前端接口类型与请求函数由 [Orval](https://orval.dev/) 根据后端 OpenAPI 文档自动生成，生成结果在 `frontend/src/api/generated/`（`endpoints.ts` + `models/`）。鉴权与 baseURL 由自定义 mutator [frontend/src/api/customFetch.ts](frontend/src/api/customFetch.ts) 注入；SSE/流式接口仍手写，不参与生成。

**更新生成代码**（需先启动后端，确保可访问 `http://localhost:9000/openapi.json`）：

```bash
cd frontend
npm run sync:api        # 拉取 openapi.json 并生成（= fetch-openapi + generate:api）
```

- 生成后可直接从 `@/api/generated/endpoints` 或 `@/api/generated/models` 引用类型与请求函数（如 `loginApiV1AuthLoginPost`、`getUserListApiV1UsersGet` 等）。
- 若后端未启动，`fetch-openapi` 会拉不到内容；可保留已有 `openapi.json` 再执行 `generate:api`。

---

## 三、同时跑前后端（开发）

开两个终端：

| 终端 1（后端）     | 终端 2（前端）   |
|-------------------|------------------|
| `cd backend && uv run python main.py` | `cd frontend && npm run dev` |

浏览器访问 <http://localhost:3000>，前端会代理 `/api` 到后端 9000 端口。

---

## 三.1、本机跑后端 + 断点调试（Cursor / VS Code）

需要打断点、单步调试时，用本机跑后端并挂上调试器：

1. **先起数据库、缓存、Celery**（二选一）：本机已装则直接开；或用 Docker：`cd backend && docker compose up -d db redis celery_worker celery_beat`（见上一节「方式 B」）。
2. **`.env` 按本机跑配置**：`DB_HOST=localhost`，`REDIS_HOST=localhost`，`REDIS_PORT=6380`（Docker 映射端口）。
3. 在 Cursor/VS Code 里按 **F5** 或 **运行 → 启动调试**，选择 **「Backend: FastAPI (debug)」**。会拉起来 uvicorn（端口 9000、`--reload`），断点会生效。

调试配置在项目根目录 [.vscode/launch.json](.vscode/launch.json)，可按需改端口或参数。

---

## 四、Docker 跑后端

### 四.1、只起数据库、缓存、Celery（本机跑 web / 调试时用）

```bash
cd backend
docker compose up -d db redis celery_worker celery_beat
```

- 只启动：**db**（PostgreSQL）、**redis**、**celery_worker**、**celery_beat**；不启动 web。本机用 `uv run python main.py` 或 F5 跑/调试 API。
- `.env` 里 `DB_HOST=localhost`、`REDIS_HOST=localhost`、`REDIS_PORT=6380`。

### 四.2、一键跑全栈后端（含 web）

按项目推荐：**Docker 一键启动**，无需在本机跑 Python/alembic。

```bash
cd backend
cp .env.example .env
# 按需改 .env（如 JWT_SECRET_KEY）；DB_* 保持与 compose 一致即可
docker compose up -d
```

- 开发环境（`APP_ENV=development`）下，web 启动时 `init_db` 会**自动建表**，无需单独跑迁移。
- 访问 <http://localhost:9000/docs>。前端 `npm run dev` 的 proxy 指向 `localhost:9000` 即可。

**需要执行 Alembic 迁移时**（例如新增了 migration 文件）：按项目习惯在本机跑，先起 db/redis 并让本机能连上（`.env` 里 `DB_HOST=localhost`，本机执行 `uv run alembic upgrade head`），详见 CLAUDE.md「数据库迁移」。

### 仅用 Docker 时出现 `password authentication failed for user "postgres"`

**原因**：PostgreSQL 只在**首次**创建数据卷时用环境变量初始化密码；日志里若出现 `PostgreSQL Database directory appears to contain a database; Skipping initialization`，说明卷里已是旧库，当前 `.env` 里的 `DB_PASSWORD` 与卷内实际密码不一致。

**修复（清空卷、用当前 .env 重新初始化）**：

1. 在 `backend` 目录下确认 `.env` 里数据库配置（之后会按这个建库）：
   - `DB_USER=postgres`
   - `DB_PASSWORD=postgres`（或你打算用的密码，**不要**再改）
   - `DB_NAME=fastapi-template-db`（与 `docker-compose.yml` 里用的名字一致即可）

2. 停掉并删除卷，再重新启动：

   ```bash
   cd backend
   docker compose down -v
   docker compose up -d
   ```

3. 等几秒后访问 <http://localhost:9000/docs>。开发环境下 web 启动时会自动建表，无需再跑 alembic。

**注意**：`docker compose down -v` 会删除 `postgres_data` 卷，库内数据会清空，仅适合开发/本机环境。
