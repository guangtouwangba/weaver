# Tasks: Fix User Data Isolation (v2 - Database-Level Isolation)

## 概述

本任务采用 **方案 A: 数据库层隔离**，在所有核心资源表添加 `user_id` 字段。

**实施顺序**：
1. Phase 1: 数据库迁移 (添加 user_id 列)
2. Phase 2: Model 层修改
3. Phase 3: Repository 层修改
4. Phase 4: API 层修改
5. Phase 5: 后台任务修改
6. Phase 6: 验证测试

---

## Phase 1: 数据库迁移

### 1.1 创建 Migration 文件

- [x] **创建 migration 文件: `20260114_103649_add_user_id_to_all_tables.py`**
  
  **文件路径**: `app/backend/alembic/versions/20260114_103649_add_user_id_to_all_tables.py`
  
  **状态**: ✅ 已完成
  - 为所有 9 个表添加 `user_id` 列 (String(255), nullable, indexed)
  - 实现了 upgrade() 和 downgrade() 函数
  - 包含通过 project_id 和 document_id 回填 user_id 的逻辑

### 1.2 执行 Migration

- [ ] **在本地/生产环境执行 migration**
  
  **命令**:
  ```bash
  cd app/backend
  alembic upgrade head
  ```
  
  **验证**:
  ```bash
  psql $DATABASE_URL -c "\\d documents" | grep user_id
  ```

---

## Phase 2: Model 层修改

### 2.1 修改 models.py

- [x] **在 DocumentModel 添加 user_id 字段** ✅
- [x] **在 ResourceChunkModel 添加 user_id 字段** ✅
- [x] **在 CanvasModel 添加 user_id 字段** ✅
- [x] **在 ChatMessageModel 添加 user_id 字段** ✅
- [x] **在 ChatMemoryModel 添加 user_id 字段** ✅
- [x] **在 ChatSummaryModel 添加 user_id 字段** ✅
- [x] **在 OutputModel 添加 user_id 字段** ✅
- [x] **在 HighlightModel 添加 user_id 字段** ✅
- [x] **在 CommentModel 添加 user_id 字段** ✅

  **文件**: `app/backend/src/research_agent/infrastructure/database/models.py`
  
  **状态**: ✅ 所有 9 个 Model 类都已添加 `user_id` 字段

### 2.2 修改 Domain Entities

- [x] **在 Document entity 添加 user_id 属性** ✅
  
  **文件**: `app/backend/src/research_agent/domain/entities/document.py`

- [x] **在 Canvas entity 添加 user_id 属性** ✅
  
  **文件**: `app/backend/src/research_agent/domain/entities/canvas.py`

- [x] **在 Output entity 添加 user_id 属性** ✅
  
  **文件**: `app/backend/src/research_agent/domain/entities/output.py`

- [x] **在 ChatMessage entity 添加 user_id 属性** ✅
  
  **文件**: `app/backend/src/research_agent/domain/entities/chat.py`
  
  **注意**: 已修复 dataclass 字段顺序问题 (非默认字段必须在默认字段之前)

- [x] **在 ResourceChunk entity 添加 user_id 属性** ✅
  
  **文件**: `app/backend/src/research_agent/domain/entities/resource_chunk.py`

---

## Phase 3: Repository 层修改

### 3.1 修改 Document Repository

- [x] **修改 sqlalchemy_document_repo.py** ✅
  
  **文件**: `app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_document_repo.py`
  
  **已完成**:
  - `save` 方法接受并设置 `user_id`
  - `find_by_project` 方法支持按 `user_id` 过滤
  - `_to_entity` 方法正确映射 `user_id`

### 3.2 修改 PgVector Store

- [x] **修改 pgvector.py** ✅
  
  **文件**: `app/backend/src/research_agent/infrastructure/vector_store/pgvector.py`
  
  **已完成**:
  - `search` 和 `hybrid_search` 方法支持 `user_id` 过滤
  - `_vector_search` 和 `_keyword_search` 内部方法支持 `user_id`

### 3.3 修改 Canvas Repository

- [x] **修改 sqlalchemy_canvas_repo.py** ✅
  
  **文件**: `app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_canvas_repo.py`
  
  **已完成**:
  - `save`, `save_with_version` 方法接受并设置 `user_id`
  - `find_by_project`, `delete_by_project` 方法支持按 `user_id` 过滤

### 3.4 修改 Output Repository

- [x] **修改 sqlalchemy_output_repo.py** ✅
  
  **文件**: `app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_output_repo.py`
  
  **已完成**:
  - `create` 方法接受并设置 `user_id`
  - `find_by_project` 方法支持按 `user_id` 过滤
  - `update` 方法支持 `user_id`

### 3.5 修改 Chat Repository

- [x] **修改 sqlalchemy_chat_repo.py** ✅
  
  **文件**: `app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_chat_repo.py`
  
  **已完成**:
  - `save` 方法接受并设置 `user_id`
  - `get_history` 方法支持按 `user_id` 过滤
  - `clear_history` 方法支持按 `user_id` 过滤

### 3.6 修改 Memory Repository

- [x] **修改 sqlalchemy_memory_repo.py** ✅
  
  **文件**: `app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_memory_repo.py`
  
  **已完成**:
  - 所有方法都支持 `user_id` 参数和过滤

### 3.7 修改 Highlight Repository

- [x] **修改 sqlalchemy_highlight_repo.py** ✅
  
  **文件**: `app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_highlight_repo.py`
  
  **已完成**:
  - `create` 方法接受并设置 `user_id`
  - `find_by_document` 方法支持按 `user_id` 过滤

### 3.8 修改 Comment Repository

- [x] **修改 sqlalchemy_comment_repo.py** ✅
  
  **文件**: `app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_comment_repo.py`
  
  **已完成**:
  - `list_by_document` 方法支持按 `user_id` 过滤
  - `count_by_document` 方法支持按 `user_id` 过滤

---

## Phase 4: API 层修改

### 4.1 修改 documents.py

- [x] **修改 documents.py 的文档创建接口** ✅
  
  **文件**: `app/backend/src/research_agent/api/v1/documents.py`
  
  **已完成**:
  - `confirm_upload` 接口传递 `user_id` 到 DocumentModel
  - `list_documents` 接口传递 `user_id` 到 use case
  - `list_highlights` 和 `create_highlight` 传递 `user_id`
  - `list_comments` 和 `create_comment` 传递 `user_id`

### 4.2 修改 chat.py

- [x] **修改 chat.py 的消息保存** ✅
  
  **文件**: `app/backend/src/research_agent/api/v1/chat.py`
  
  **已完成**:
  - `stream_message` 接口传递 `user_id` 到 `StreamMessageInput`
  - 配置获取使用 `user_id`

### 4.3 修改 outputs.py

- [x] **修改 outputs.py 的生成接口** ✅
  
  **文件**: `app/backend/src/research_agent/api/v1/outputs.py`
  
  **已完成**:
  - `generate_output` 接口传递 `user_id`
  - `list_outputs`, `get_output`, `delete_output`, `update_output` 传递 `user_id`
  - `expand_node`, `synthesize_nodes` 传递 `user_id`

### 4.4 修改 canvas.py

- [x] **修改 canvas.py 的保存接口** ✅
  
  **文件**: `app/backend/src/research_agent/api/v1/canvas.py`
  
  **已完成**:
  - 所有 canvas 相关接口传递 `user_id` 到 use cases

### 4.5 修改 Canvas Use Cases

- [x] **修改所有 Canvas Use Cases** ✅
  
  **已完成的文件**:
  - `create_node.py` - 支持 `user_id`
  - `save_canvas.py` - 支持 `user_id`
  - `get_canvas.py` - 支持 `user_id`
  - `update_node.py` - 支持 `user_id`
  - `delete_node.py` - 支持 `user_id`
  - `clear_canvas.py` - 支持 `user_id`
  
  **注意**: 已修复所有 `Optional` 类型注解为 `| None` 格式

---

## Phase 5: 后台任务修改

### 5.1 修改 Document Processor

- [x] **修改 document_processor.py** ✅
  
  **文件**: `app/backend/src/research_agent/worker/tasks/document_processor.py`
  
  **已完成**:
  - `_save_chunks_batch` 方法从 DocumentModel 获取 `user_id`
  - 创建 ResourceChunk 时传递 `user_id`

### 5.2 修改 Output Generation Service

- [x] **修改 output_generation_service.py** ✅
  
  **文件**: `app/backend/src/research_agent/application/services/output_generation_service.py`
  
  **已完成**:
  - 所有方法支持 `user_id` 参数
  - 清理了重复的方法定义

### 5.3 修改 Stream Message Use Case

- [x] **修改 stream_message.py** ✅
  
  **文件**: `app/backend/src/research_agent/application/use_cases/chat/stream_message.py`
  
  **已完成**:
  - `StreamMessageInput` 包含 `user_id`
  - 传递 `user_id` 到 ContextEngine, ChatRepository, PGVectorRetriever 等

### 5.4 修改 Memory Service

- [x] **修改 memory_service.py** ✅
  
  **文件**: `app/backend/src/research_agent/domain/services/memory_service.py`
  
  **已完成**:
  - 所有方法支持 `user_id` 参数

---

## Phase 6: 验证测试

### 6.1 数据库验证

- [ ] **验证 migration 正确执行**
  
  **命令**:
  ```bash
  psql $DATABASE_URL -c "
    SELECT table_name 
    FROM information_schema.columns 
    WHERE column_name = 'user_id' 
    AND table_schema = 'public'
    ORDER BY table_name;
  "
  ```
  
  **预期结果**: 应该看到以下表:
  - canvases
  - chat_memories
  - chat_messages
  - chat_summaries
  - comments
  - documents
  - highlights
  - outputs
  - resource_chunks

### 6.2 数据完整性验证

- [ ] **验证 user_id 已正确回填**
  
  **命令**:
  ```sql
  SELECT 'documents' as table_name, COUNT(*) as null_count 
  FROM documents WHERE user_id IS NULL
  UNION ALL
  SELECT 'resource_chunks', COUNT(*) FROM resource_chunks WHERE user_id IS NULL
  UNION ALL
  SELECT 'canvases', COUNT(*) FROM canvases WHERE user_id IS NULL
  UNION ALL
  SELECT 'chat_messages', COUNT(*) FROM chat_messages WHERE user_id IS NULL
  UNION ALL
  SELECT 'outputs', COUNT(*) FROM outputs WHERE user_id IS NULL;
  ```

### 6.3 功能测试

- [ ] **测试文档上传设置 user_id**
  
  1. 使用 User A 登录
  2. 上传一个文档
  3. 检查数据库: `SELECT user_id FROM documents ORDER BY created_at DESC LIMIT 1;`
  4. 验证 user_id 与登录用户一致

- [ ] **测试 Chat 消息设置 user_id**
  
  1. 使用 User A 登录
  2. 发送一条聊天消息
  3. 检查数据库: `SELECT user_id FROM chat_messages ORDER BY created_at DESC LIMIT 1;`
  4. 验证 user_id 与登录用户一致

- [ ] **测试 Output 生成设置 user_id**
  
  1. 使用 User A 登录
  2. 生成一个 mindmap
  3. 检查数据库: `SELECT user_id FROM outputs ORDER BY created_at DESC LIMIT 1;`
  4. 验证 user_id 与登录用户一致

### 6.4 隔离测试

- [ ] **测试用户隔离**
  
  1. 使用 User A 创建项目和文档
  2. 使用 User B 尝试访问 User A 的资源
  3. 验证返回 403 Forbidden
  4. 验证数据库查询不返回 User A 的数据

---

## 完成标准

- [x] 所有 9 个表都添加了 `user_id` 列和索引 (Schema/Model 层)
- [ ] 所有历史数据都已回填 `user_id` (需要执行 migration)
- [x] 新创建的资源都会设置 `user_id` (代码已实现)
- [x] 查询方法都支持按 `user_id` 过滤 (代码已实现)
- [ ] 功能测试通过
- [ ] 用户隔离测试通过

---

## 代码质量修复

在实施过程中，还修复了以下代码质量问题：

- [x] 修复 `Optional` 类型注解为 `| None` 格式
- [x] 修复 `List`/`Dict` 为 `list`/`dict` 格式
- [x] 修复 dataclass 字段顺序问题 (chat.py)
- [x] 移除未使用的导入
- [x] 修复 f-string 无占位符警告
- [x] 清理重复的方法定义 (output_generation_service.py)
