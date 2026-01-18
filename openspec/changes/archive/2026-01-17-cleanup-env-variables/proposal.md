# Cleanup Environment Variables

## Status
Draft

## Why

项目中存在多个环境变量配置问题：

### 1. 重复定义的变量

| 变量 | 位置 | 问题 |
|------|------|------|
| `SUPABASE_URL` | backend env.example | 与 `NEXT_PUBLIC_SUPABASE_URL` 实际指向同一地址 |
| `NEXT_PUBLIC_SUPABASE_URL` | backend env.example, root env.example | 主要用于前端，但后端也在使用 |

**分析**: 后端使用 `SUPABASE_URL`，前端使用 `NEXT_PUBLIC_SUPABASE_URL`。虽然值相同，但这是 Next.js 的设计要求（`NEXT_PUBLIC_` 前缀用于客户端暴露）。这不是真正的重复，而是架构需要。

### 2. 在 env.example 中定义但代码中未使用的变量

| 变量 | 文件 | 状态 |
|------|------|------|
| `DB_POOL_SIZE` | backend/env.example | 未在 config.py 或代码中使用 |
| `DB_MAX_OVERFLOW` | backend/env.example | 未在 config.py 或代码中使用 |
| `LLM_PROVIDER` | backend/env.example | 未在 config.py 中定义 |
| `LLM_TEMPERATURE` | backend/env.example | 未在 config.py 中定义 |
| `LLM_MAX_TOKENS` | backend/env.example | 未在 config.py 中定义 |
| `EMBEDDING_PROVIDER` | backend/env.example | 未在 config.py 中定义 |
| `EMBEDDING_DIMENSIONS` | backend/env.example | 未在 config.py 或代码中使用 |
| `FAKE_EMBEDDING_SIZE` | backend/env.example | 未在代码中使用 |
| `OPENROUTER_SITE_URL` | backend/env.example | 未在代码中使用 |
| `OPENROUTER_SITE_NAME` | backend/env.example | 未在代码中使用 |
| `OPENAI_BASE_URL` | backend/env.example | 未在 config.py 中定义 |
| `RUNTIME_EVALUATION_*` (6个) | backend/env.example | 未在代码中使用，与 `evaluation_enabled` 功能不匹配 |

### 3. 根目录 env.example 冗余

根目录的 `env.example` 标注为 "legacy"，但仍包含部分变量定义，可能导致混淆。

## What

清理环境变量配置：
1. 从 `backend/env.example` 移除未使用的变量
2. 简化或移除根目录的 `env.example`
3. 确保 env.example 与 config.py 保持同步

## Related

无

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-01-16 | 保留 SUPABASE_URL 和 NEXT_PUBLIC_SUPABASE_URL | 不是重复，是 Next.js 架构需求 |
| 2024-01-16 | 移除未使用的 RUNTIME_EVALUATION_* 变量 | 代码使用 evaluation_enabled 而非这些变量 |
