# YiDao 易道 — 前端

React 19 + TypeScript + Vite + Tailwind + shadcn/ui；API 客户端由 Orval 根据后端 OpenAPI 自动生成。

## 怎么跑

详见仓库根 [RUN.md](../RUN.md)。

```bash
npm install
npm run dev          # 开发：http://localhost:3000，/api 代理到后端 9000
npm run build        # 生产构建
npm run sync:api     # 更新 API 类型与请求（需后端起好，见 RUN.md）
```

## 技术栈

- Vite · React 19 · TypeScript · Tailwind CSS v4 · shadcn/ui
- Zustand · TanStack Query · React Router v7 · react-hook-form + zod
