# Change: Cleanup Database Schema

## Why
数据库中存在多个历史遗留表，是产品探索不同方向时创建的。
现在将项目视为 **全新项目**，删除所有旧的 migration 文件，创建新的干净 schema。

## What Changes

### **BREAKING CHANGE**: 完全重建数据库 Schema

#### 删除所有现有 Migrations
删除 `alembic/versions/` 下的所有 36 个 migration 文件。

#### 创建新的 Initial Schema
创建单一的 `20260114_000001_initial_schema.py`，仅包含当前实际使用的表。

### 保留的表 (包含在新 Schema 中)

| 表名 | 说明 |
|------|------|
| `projects` | 项目主表 |
| `documents` | 文档表 |
| `resource_chunks` | **统一资源 Chunks** (替代 document_chunks) |
| `canvases` | Canvas 数据 |
| `chat_messages` | 聊天消息 |
| `chat_memories` | 聊天记忆 (Long-term Episodic) |
| `chat_summaries` | 聊天摘要 (Short-term Working) |
| `task_queue` | 后台任务队列 |
| `pending_cleanups` | 异步文件清理 |
| `outputs` | 生成的输出 (mindmap, summary) |
| `url_contents` | URL 内容提取 |
| `highlights` | PDF 批注 |
| `comments` | 文档评论 |
| `tags` | 标签 |
| `inbox_items` | 收件箱项目 |
| `inbox_item_tags` | 收件箱-标签关联 |
| `api_keys` | API 密钥 |
| `global_settings` | 全局设置 |
| `project_settings` | 项目设置 |
| `user_settings` | 用户设置 |
| `evaluation_logs` | RAG 评估日志 |

### 删除的表 (不包含在新 Schema 中)

| 表名 | 原因 |
|------|------|
| `document_chunks` | 已被 `resource_chunks` 替代 |
| `entities` | Knowledge Graph 探索后未使用 |
| `relations` | Knowledge Graph 探索后未使用 |

### 代码清理
- 删除 `EntityModel`, `RelationModel`, `DocumentChunkModel` 从 `models.py`
- 更新相关依赖代码

### Supabase SQL 清理脚本
在部署前，需要在 Supabase SQL Editor 中执行以下脚本来清理旧数据库：

```sql
-- =============================================================================
-- Supabase Database Reset Script
-- 执行前请确保已备份重要数据！
-- =============================================================================

-- Step 1: 清除 alembic_version 表（防止 migration version 冲突）
TRUNCATE TABLE IF EXISTS alembic_version;

-- Step 2: 删除所有现有表（按依赖顺序）
DROP TABLE IF EXISTS inbox_item_tags CASCADE;
DROP TABLE IF EXISTS inbox_items CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS url_contents CASCADE;
DROP TABLE IF EXISTS outputs CASCADE;
DROP TABLE IF EXISTS pending_cleanups CASCADE;
DROP TABLE IF EXISTS evaluation_logs CASCADE;
DROP TABLE IF EXISTS user_settings CASCADE;
DROP TABLE IF EXISTS project_settings CASCADE;
DROP TABLE IF EXISTS global_settings CASCADE;
DROP TABLE IF EXISTS chat_summaries CASCADE;
DROP TABLE IF EXISTS chat_memories CASCADE;
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS task_queue CASCADE;
DROP TABLE IF EXISTS relations CASCADE;
DROP TABLE IF EXISTS entities CASCADE;
DROP TABLE IF EXISTS comments CASCADE;
DROP TABLE IF EXISTS highlights CASCADE;
DROP TABLE IF EXISTS resource_chunks CASCADE;
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS canvases CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS projects CASCADE;

-- Step 3: 删除 alembic_version 表本身
DROP TABLE IF EXISTS alembic_version CASCADE;

-- Step 4: 确保 pgvector extension 存在
CREATE EXTENSION IF NOT EXISTS vector;

-- 完成！现在可以运行 alembic upgrade head
```

## Impact
- **BREAKING CHANGE**: 现有数据库需要完全重建，所有数据将丢失
- 新部署只需运行 `alembic upgrade head` 一次
- 代码更简洁，无历史包袱
