---
name: yidao-tech-stack
description: Declares YiDao project's core tech stack with pinned versions and official documentation URLs. Ensures AI-generated code follows version-compatible best practices. Use when implementing any feature, writing code, choosing libraries, or making technical decisions in the YiDao project.
---

# YiDao Tech Stack

When implementing features, use ONLY the libraries and versions listed here. If you need API-level documentation, use the context7 MCP (see below).

## Looking Up Documentation

Use the `user-context7Mcp` MCP server to get version-accurate API docs before writing non-trivial code:

```
Step 1: CallMcpTool(server="user-context7Mcp", toolName="resolve-library-id", arguments={libraryName: "langgraph", query: "how to define StateGraph"})
Step 2: CallMcpTool(server="user-context7Mcp", toolName="query-docs", arguments={libraryId: "<result from step 1>", query: "how to define StateGraph with conditional edges"})
```

Do NOT guess APIs from training data when context7 can provide current docs.

---

## Backend: Existing Infrastructure

All code in `backend/`. Fully async architecture. See `backend/CLAUDE.md` for patterns.

### Core

- **Python** >=3.12 — https://docs.python.org/3.12/
- **FastAPI** >=0.128.0 — https://fastapi.tiangolo.com/
- **Pydantic** >=2.12.0 — https://docs.pydantic.dev/latest/
- **pydantic-settings** >=2.12.0 — https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- **uvicorn** >=0.40.0 — https://www.uvicorn.org/
- **gunicorn** >=23.0.0 — https://docs.gunicorn.org/en/stable/

### Database & ORM

- **PostgreSQL** 16 — https://www.postgresql.org/docs/16/
- **SQLAlchemy** >=2.0.45 (async mode) — https://docs.sqlalchemy.org/en/20/
- **asyncpg** >=0.31.0 — https://magicstack.github.io/asyncpg/
- **Alembic** >=1.18.0 — https://alembic.sqlalchemy.org/en/latest/

### Cache & Queue

- **Redis** (python) >=4.2.0,<5.0.0 — https://redis.readthedocs.io/en/stable/
- **Celery** >=5.6.0 — https://docs.celeryq.dev/en/stable/
- **fastapi-cache2** >=0.2.0 — https://github.com/long2ice/fastapi-cache

### Auth

- **python-jose** >=3.5.0 — https://python-jose.readthedocs.io/
- **passlib** >=1.7.4 — https://passlib.readthedocs.io/

### Observability

- **OpenTelemetry** >=1.39.0 — https://opentelemetry.io/docs/languages/python/
- **prometheus-client** >=0.24.0 — https://prometheus.io/docs/
- **slowapi** >=0.1.9 — https://github.com/laurentS/slowapi

### Dev & Test

- **pytest** >=7.4.0 — https://docs.pytest.org/
- **pytest-asyncio** >=0.23.0 — https://pytest-asyncio.readthedocs.io/
- **httpx** >=0.25.0 — https://www.python-httpx.org/
- **ruff** >=0.1.0 — https://docs.astral.sh/ruff/
- **mypy** >=1.7.0 — https://mypy.readthedocs.io/
- **uv** (package manager) — https://docs.astral.sh/uv/

---

## Backend: AI Layer (New)

These are added to `backend/pyproject.toml` for YiDao's AI coaching features.

- **LangGraph** — https://langchain-ai.github.io/langgraph/
  - Agent orchestration, state machine, checkpoint/persistence
- **langchain-core** — https://python.langchain.com/docs/
  - Base types (messages, chat models, runnables)
- **langchain-openai** — https://python.langchain.com/docs/integrations/chat/openai/
  - `ChatOpenAI` for DeepSeek and all OpenAI-compatible APIs
- **langgraph-checkpoint-postgres** — https://langchain-ai.github.io/langgraph/reference/checkpoints/
  - Persistent checkpointing using existing PostgreSQL
- **Langfuse** — https://langfuse.com/docs
  - LLM observability, tracing, prompt management

### AI Layer Constraints

- MVP uses **DeepSeek** only: `ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1")`
- No `langchain-anthropic` yet. Add later when Claude is needed.
- No RAG, no vector DB, no embeddings for MVP. Pattern Skills stored in PostgreSQL `pattern_skills` table (JSONB), managed via Admin API.
- LangGraph checkpoint uses PostgreSQL (same instance as app DB).

---

## Frontend

SPA architecture. No SSR, no Next.js. Static build deployable to nginx/CDN.

### Core

- **React** 19 — https://react.dev/
- **TypeScript** — https://www.typescriptlang.org/docs/
- **Vite** — https://vite.dev/guide/

### Styling & Components

- **Tailwind CSS** v4 — https://tailwindcss.com/docs
- **shadcn/ui** — https://ui.shadcn.com/docs
- **lucide-react** — https://lucide.dev/guide/packages/lucide-react

### State & Data

- **Zustand** — https://zustand.docs.pmnd.rs/
- **TanStack Query** — https://tanstack.com/query/latest/docs/

### Routing

- **React Router** v7 — https://reactrouter.com/

### Content & Forms

- **react-markdown** — https://github.com/remarkjs/react-markdown
- **remark-gfm** — https://github.com/remarkjs/remark-gfm
- **react-hook-form** — https://react-hook-form.com/docs
- **zod** — https://zod.dev/

### Code Quality

- **ESLint** — https://eslint.org/docs/latest/
- **Prettier** — https://prettier.io/docs/

### Frontend Constraints

- Pure SPA, no Node.js server required at runtime.
- Chat streaming uses native `fetch` + `ReadableStream` consuming FastAPI SSE.
- Coach output is structured (sections + action cards), not plain text. Design components accordingly.

---

## Coding Standards

### Mandatory Rules

1. **Async everything** (backend): All DB ops, service methods, and route handlers must be `async def`.
2. **context7 first**: Before writing code that calls a library API, look up the docs via `user-context7Mcp` to ensure version-accurate usage.
3. **No extra libraries**: Do not introduce new dependencies without explicit approval. Use what's listed here.
4. **Version pinning**: Backend versions are in `backend/pyproject.toml`. Respect minimum version constraints.

### General

- Code identifiers in English. Comments in Chinese when clarifying domain-specific logic.
- Type annotations everywhere — Python type hints, TypeScript `strict: true`.
- No magic numbers or strings. Use enums or named constants.
- One module = one responsibility. Prefer many small files over few large ones.
- Functions under 40 lines, files under 300 lines. Extract early.

### Backend Conventions

Follow `backend/CLAUDE.md` for all existing backend patterns. Summary of key conventions:

**Layered architecture** (strict, no skipping layers):

```
API (app/api/)  →  Service (app/services/)  →  Repository (app/repository/)  →  Model (app/models/)
```

**Naming** (established in existing codebase):

- Repository: `add()`, `find_by_id()`, `find_by_*()`, `find_all()`, `find_paginated()`, `update_by_id()`, `remove_by_id()`
- API routes: `add_*()`, `get_*_detail()`, `get_*_list()`, `update_*_by_id()`, `remove_*_by_id()`
- Pydantic schemas: `{Entity}Create`, `{Entity}Update`, `{Entity}Response`

**Error handling**: Raise `AppException` subclasses (in `app/exceptions/`), never return error dicts.

### Backend: AI Layer Conventions

**File organization** for new AI module:

```
app/ai/
├── graph.py              # LangGraph graph definition + compilation
├── state.py              # Graph state Pydantic model (single source of truth)
├── nodes/                # One file per graph node
│   ├── parse_agent.py
│   ├── case_manager.py
│   ├── bucket_update.py
│   ├── pattern_skill.py
│   ├── coach_agent.py
│   ├── safety.py
│   └── render.py
├── schemas/              # AI-specific Pydantic models (parse_result, coach_output)
└── llm.py                # Model factory function (get_llm)
```

**LangGraph nodes**: verb_noun pattern — `parse_message`, `select_bucket`, `update_bucket`, `render_reply`.

**Structured output**: Always use `.with_structured_output(PydanticModel)`. Never parse raw JSON strings manually.

**Prompts**: Managed via Langfuse Prompt Management. Code fetches prompts by name using Langfuse SDK. Fallback constants in `app/ai/prompts/` for local dev / when Langfuse is unavailable. Never inline prompt strings in node functions.

**Pattern Skills**: Stored in PostgreSQL `pattern_skills` table (JSONB columns). Managed via Admin CRUD API (`/api/v1/admin/skills`). Use Redis cache (existing `fastapi-cache2`) for hot path. Initial data imported via Alembic data migration or seed script.

**Graph state**: Define a single Pydantic model in `state.py`. All nodes read from and write to this shared state.

### Frontend Conventions

**File structure**:

```
src/
├── components/           # Reusable UI components
│   ├── ui/              # shadcn/ui base components (auto-generated)
│   ├── chat/            # Chat-specific (ChatBubble, ChatInput, CoachCard)
│   └── layout/          # Header, Sidebar, PageContainer
├── pages/               # Route page components
├── hooks/               # Custom hooks (useChatStream, useBuckets)
├── stores/              # Zustand stores (chatStore, authStore)
├── api/                 # API client + TanStack Query hooks
│   ├── client.ts        # Fetch/axios instance with auth interceptor
│   └── queries/         # One file per domain (useAuth, useChat, useBuckets)
├── types/               # Shared TypeScript types (mirrors backend schemas)
├── lib/                 # Utility functions (cn, formatDate, etc.)
└── config/              # App constants, env config
```

**Naming**:

- PascalCase for components: `ChatBubble.tsx`, `BucketSidebar.tsx`
- camelCase for hooks: `useChatStream.ts`, `useBuckets.ts`
- camelCase for stores: `chatStore.ts`, `authStore.ts`
- PascalCase for pages: `ChatPage.tsx`, `LoginPage.tsx`
- PascalCase for types: `BucketResponse`, `CoachOutput`

**State management**:

- **Zustand** — client-only state: active bucket ID, sidebar toggle, input draft, UI flags
- **TanStack Query** — all server data: bucket list, chat history, user profile
- Never duplicate server data in Zustand. If it comes from an API, it belongs in TanStack Query's cache.

**Components**:

- Keep components under 150 lines. Extract sub-components early.
- Props interface defined at top of file, named `{Component}Props`.
- Use `cn()` utility (from shadcn/ui `lib/utils`) for conditional Tailwind class merging.
- Colocate related components in the same directory with an `index.ts` barrel export.

**TypeScript**:

- `strict: true` in tsconfig. No exceptions.
- Prefer `interface` for object shapes, `type` for unions and intersections.
- No `any`. Use `unknown` + type narrowing when type is uncertain.
- API response types in `src/types/` should mirror backend Pydantic schemas exactly.

**Styling**:

- Tailwind utility classes only. No custom CSS files unless absolutely unavoidable.
- Mobile-first responsive: base styles for mobile, `md:` for tablet, `lg:` for desktop.
- Dark mode via `dark:` variant (shadcn/ui supports it natively).

**API calls**:

- All HTTP requests go through a single configured client in `src/api/client.ts`.
- Auth token injected via interceptor. 401 triggers token refresh or redirect to login.
- TanStack Query hooks wrap every API call. Components never call `fetch` directly.
- **Exception**: SSE streaming (chat) uses a custom hook (`useChatStream`) with native `fetch` + `ReadableStream`, because TanStack Query is not designed for long-lived streams.
