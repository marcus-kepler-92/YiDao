# YiDao 易道

对话式生活分析与人本教练助手。后端 FastAPI + PostgreSQL + Redis + Celery；前端 React 19 + Vite + TypeScript；AI 层 LangGraph + LangChain（DeepSeek 等）。

## 怎么跑

详见 **[RUN.md](RUN.md)**。

- **后端**：`cd backend && cp .env.example .env` 后，Docker 一键 `docker compose up -d`（端口 9000），或本机 `uv sync` + 起 db/redis 后 `uv run python main.py`。
- **前端**：`cd frontend && npm install && npm run dev`（端口 3000，代理 `/api` 到后端）。
- **API 客户端生成**：后端起好后在 frontend 下执行 `npm run sync:api`。

## 目录

- `backend/` — FastAPI 后端（含 AI 图、Pattern Skills CRUD），见 [backend/README.md](backend/README.md)。
- `frontend/` — React SPA，见 [frontend/README.md](frontend/README.md)。
- [.cursor/skills/yidao-tech-stack/](.cursor/skills/yidao-tech-stack/) — 项目技术栈与编码约定。
