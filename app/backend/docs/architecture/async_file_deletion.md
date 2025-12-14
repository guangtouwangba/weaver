# 异步文件删除设计方案

## 概述

本文档记录了文件删除功能从同步改为异步的设计方案，包括不同方案的 trade-off 分析和最终实现选择。

## 问题背景

原始的文件删除流程是同步的：

```
用户请求 → 删除Supabase文件 → 删除Chunks → 删除本地文件 → 删除DB记录 → 返回响应
           |_________________________ 全部等待完成 __________________________|
```

**痛点**:
- 响应时间长（~500ms）：需要等待远程存储（Supabase）的网络IO
- 用户体验差：删除操作感觉"卡顿"
- 如果远程删除失败，整个操作可能失败或留下孤立记录

---

## 方案对比

### 方案一：Soft Delete + Background Job

```
用户请求 → 标记为deleted → 立即返回(~10ms)
                 ↓
        后台任务队列异步清理物理资源
```

**实现要点**：
- Document 表添加 `deleted_at` 和 `deletion_status` 字段
- API 返回 202 Accepted
- 使用任务队列（如 Celery）处理后台删除

| 优点 | 缺点 |
|------|------|
| ✅ 用户体验极佳（即时响应） | ❌ 需要引入任务队列（如 Celery/RQ/Dramatiq） |
| ✅ 可重试失败的删除 | ❌ 系统复杂度增加 |
| ✅ 批量删除更高效 | ❌ 需要处理"删除中"的中间状态 |
| ✅ 支持撤销删除（在物理删除前） | ❌ 前端需要处理 202 状态 |

**适用场景**：大规模生产系统，需要高可靠性和可观测性

---

### 方案二：Fire-and-Forget + 定期清理兜底 ✅ 已选择

```
用户请求 → 记录pending_cleanup → 删除DB记录 → 返回 → 异步清理文件
                                                        ↓
                                              定时任务重试失败的清理
```

**实现要点**：
- 新增 `pending_cleanups` 表记录待清理文件
- 删除 API 立即删除数据库记录
- 使用 `asyncio.create_task()` 异步清理文件
- 定时任务扫描并重试失败的清理

| 优点 | 缺点 |
|------|------|
| ✅ 实现简单，无需额外依赖 | ❌ 异步任务无法监控状态 |
| ✅ 响应更快（~50ms vs ~500ms） | ❌ 可能留下短暂的孤立文件 |
| ✅ 对现有架构改动小 | ❌ 需要定期任务兜底 |
| ✅ 使用现有任务队列基础设施 | |

**适用场景**：中小规模系统，追求简单实用

---

### 方案三：Event-Driven（事件驱动）

```python
# 发布删除事件
await event_bus.publish(DocumentDeletedEvent(...))

# 多个消费者独立处理
@event_handler(DocumentDeletedEvent)
async def cleanup_supabase(event): ...

@event_handler(DocumentDeletedEvent)
async def cleanup_local(event): ...
```

| 优点 | 缺点 |
|------|------|
| ✅ 解耦，易扩展 | ❌ 需要事件总线基础设施 |
| ✅ 各清理任务独立，互不阻塞 | ❌ 调试复杂 |
| ✅ 便于添加新的清理逻辑 | ❌ 事件丢失风险 |

**适用场景**：微服务架构，事件驱动系统

---

## 最终选择：方案二

选择理由：
1. **实现成本低**：不需要引入 Celery 等重型依赖
2. **用户体验提升明显**：删除响应从 ~500ms 降到 ~50ms
3. **兼容现有架构**：复用已有的 TaskQueue 系统
4. **可靠性保证**：定时任务兜底确保最终一致性
5. **可扩展性**：为未来可能的任务队列升级留有空间

---

## 实现细节

### 1. 数据模型

新增 `pending_cleanups` 表：

```sql
CREATE TABLE pending_cleanups (
    id UUID PRIMARY KEY,
    file_path VARCHAR(512) NOT NULL,
    storage_type VARCHAR(50) DEFAULT 'both',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 5,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    document_id UUID,
    project_id UUID
);
```

### 2. 删除流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     DELETE /documents/{id}                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ 1. 记录 pending_cleanup │
                   └─────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ 2. 删除 chunks (同步) │
                   └─────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ 3. 删除 document (同步) │
                   └─────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ 4. 返回 204 No Content │
                   └─────────────────────┘
                              │
                              ▼ (后台)
                   ┌─────────────────────┐
                   │ 5. Fire-and-forget   │
                   │    清理物理文件       │
                   └─────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                              ▼
        ┌────────────┐                ┌────────────┐
        │ 成功: 删除   │                │ 失败: 更新   │
        │ pending记录 │                │ attempts   │
        └────────────┘                └────────────┘
```

### 3. 定期清理

提供两种触发方式：

1. **API 端点**（适合外部 cron 调用）:
   ```
   POST /api/v1/maintenance/cleanup/trigger
   ```

2. **任务队列**（内部调度）:
   ```python
   TaskType.FILE_CLEANUP
   ```

建议配置 cron 每天凌晨执行一次：
```bash
0 3 * * * curl -X POST http://localhost:8000/api/v1/maintenance/cleanup/trigger
```

### 4. 监控

查看清理队列状态：
```
GET /api/v1/maintenance/cleanup/status
GET /api/v1/maintenance/cleanup/pending
```

---

## 相关文件

- `app/backend/src/research_agent/infrastructure/database/models.py` - PendingCleanupModel
- `app/backend/src/research_agent/domain/repositories/pending_cleanup_repo.py` - Repository 接口
- `app/backend/src/research_agent/application/services/async_cleanup_service.py` - 清理服务
- `app/backend/src/research_agent/api/v1/documents.py` - 删除 API
- `app/backend/src/research_agent/api/v1/maintenance.py` - 维护 API
- `app/backend/src/research_agent/worker/tasks/file_cleanup.py` - 清理任务

---

## 参考

- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Eventual Consistency Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/eventual-consistency)
