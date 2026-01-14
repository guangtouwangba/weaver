# Fix User Data Isolation (v2)

## Problem Statement

当前系统存在用户数据隔离问题：

- **User A 可以看到 User B 的内容**
- **根本原因**: 只在 `ProjectModel` 有 `user_id` 字段，其他资源表（documents, chunks, outputs 等）没有 `user_id`
- **风险**: API 层验证可能被遗漏，后台任务可能绕过验证

## Root Cause Analysis

### 当前架构问题

```
┌──────────────────────────────────────────────────────┐
│  API Layer (get_verified_project)                    │  ← 唯一的保护层
├──────────────────────────────────────────────────────┤
│  Database Layer                                      │  ← 没有 user_id
│  ┌─────────┐  ┌──────────┐  ┌────────────────┐      │
│  │documents│  │  outputs │  │ resource_chunks│      │
│  │ ❌ no   │  │  ❌ no   │  │    ❌ no       │      │
│  │ user_id │  │  user_id │  │   user_id      │      │
│  └─────────┘  └──────────┘  └────────────────┘      │
└──────────────────────────────────────────────────────┘
```

### 风险场景

1. **开发者遗漏**: 新增 API 忘记加 `get_verified_project`
2. **后台任务**: Worker 直接操作数据库，无 API 层保护
3. **管理脚本**: 数据迁移脚本可能泄露数据
4. **SQL 注入**: 攻击者可能绕过 API 层查询

## Proposed Solution

### 方案 A: 数据库层隔离 (已采用)

在 **所有核心资源表** 添加 `user_id` 字段：

```
┌──────────────────────────────────────────────────────┐
│  Layer 1: API Layer (get_verified_project)           │
├──────────────────────────────────────────────────────┤
│  Layer 2: Database Layer (user_id on every table)    │
│  ┌─────────┐  ┌──────────┐  ┌────────────────┐      │
│  │documents│  │  outputs │  │ resource_chunks│      │
│  │ ✅      │  │  ✅      │  │    ✅          │      │
│  │ user_id │  │  user_id │  │   user_id      │      │
│  └─────────┘  └──────────┘  └────────────────┘      │
└──────────────────────────────────────────────────────┘
```

### 需要修改的表

| 表名 | 优先级 | 说明 |
|------|--------|------|
| `documents` | P0 | 用户文档 |
| `resource_chunks` | P0 | RAG 检索数据 |
| `outputs` | P0 | 生成内容 |
| `canvases` | P0 | 画布数据 |
| `chat_messages` | P0 | 对话历史 |
| `chat_memories` | P1 | 对话记忆 |
| `chat_summaries` | P1 | 对话摘要 |
| `highlights` | P2 | 文档标注 |
| `comments` | P2 | 文档评论 |

## User Review Required

> [!IMPORTANT]
> **Breaking Changes**:
> - 需要运行数据库 migration
> - Repository 接口签名变更（添加 user_id 参数）
> - 后台任务需要传递 user_id

> [!WARNING]
> **Migration 注意事项**:
> - Migration 会回填所有历史数据的 user_id
> - 生产环境执行前建议备份数据库

## Implementation Overview

### Phase 1: Database Migration
- 创建 migration 添加 user_id 列
- 从 project.user_id 回填历史数据

### Phase 2: Model Layer
- 在 9 个 ORM Model 添加 user_id 字段
- 更新 Domain Entities

### Phase 3: Repository Layer
- 修改创建方法，接受 user_id 参数
- 修改查询方法，支持 user_id 过滤

### Phase 4: API Layer
- 确保所有接口传递 user_id 到 Repository

### Phase 5: Background Tasks
- 修改后台任务，从 project 获取 user_id 并传递

### Phase 6: Verification
- 数据库验证
- 功能测试
- 隔离测试

## Affected Files

### Database
- `alembic/versions/XXXXXX_add_user_id_to_all_tables.py` [NEW]

### Models
- `infrastructure/database/models.py` [MODIFY]
- `domain/entities/document.py` [MODIFY]
- `domain/entities/canvas.py` [MODIFY]
- `domain/entities/output.py` [MODIFY]
- `domain/entities/chat.py` [MODIFY]
- `domain/entities/resource_chunk.py` [MODIFY]

### Repositories
- `infrastructure/database/repositories/sqlalchemy_document_repo.py` [MODIFY]
- `infrastructure/database/repositories/sqlalchemy_canvas_repo.py` [MODIFY]
- `infrastructure/database/repositories/sqlalchemy_output_repo.py` [MODIFY]
- `infrastructure/vector_store/pg_vector.py` [MODIFY]

### API
- `api/v1/documents.py` [MODIFY]
- `api/v1/chat.py` [MODIFY]
- `api/v1/outputs.py` [MODIFY]
- `api/v1/canvas.py` [MODIFY]

### Background Tasks
- `application/use_cases/documents/process_document.py` [MODIFY]
- `application/use_cases/outputs/generate_mindmap.py` [MODIFY]
- `application/use_cases/outputs/generate_summary.py` [MODIFY]

## Timeline Estimate

- Phase 1 (Migration): 1 hour
- Phase 2 (Models): 0.5 hour
- Phase 3 (Repositories): 2 hours
- Phase 4 (API): 1 hour
- Phase 5 (Background Tasks): 1 hour
- Phase 6 (Verification): 1 hour

**Total: ~6.5 hours**
