# Spec: Background Tasks User Isolation

## ADDED Requirements

### Requirement: Pass User ID in Background Tasks

The system SHALL use `user_id` in all background tasks when creating or accessing resources.

#### Scenario: Verify Background Task uses user_id
- **WHEN** a background task is executed
- **THEN** the `user_id` SHALL be used for resource creation

---

## 背景

后台任务（如文档处理、Output 生成）不经过 API 层，直接访问数据库。
因此需要在任务中主动获取 `user_id` 并传递给 Repository。

**获取 user_id 的方法**: 从 project 表获取

```python
# 通用模式
project = await project_repo.find_by_id(project_id)
user_id = project.user_id if project else None
```

---

## 1. Document Processor

### 文件路径

找到处理文档的文件，可能是以下位置之一：
- `app/backend/src/research_agent/application/use_cases/documents/process_document.py`
- `app/backend/src/research_agent/application/use_cases/documents/processor.py`
- `app/backend/src/research_agent/infrastructure/document/processor.py`

### 修改 1: 处理函数

**找到方法**: 搜索 `async def process_document` 或 `async def process`

**当前代码模式**:
```python
async def process_document(
    document_id: UUID,
    project_id: UUID,
    session: AsyncSession,
):
    # ... 解析文档
    # ... 创建 chunks
    await vector_store.add_chunks(
        chunks=chunks,
        project_id=project_id,
        resource_id=document_id,
        resource_type="document",
    )
```

**修改为**:
```python
async def process_document(
    document_id: UUID,
    project_id: UUID,
    session: AsyncSession,
):
    # ✅ Step 1: 获取 project 以得到 user_id
    from research_agent.infrastructure.database.repositories.sqlalchemy_project_repo import (
        SQLAlchemyProjectRepository,
    )
    project_repo = SQLAlchemyProjectRepository(session)
    project = await project_repo.find_by_id(project_id)
    user_id = project.user_id if project else None
    
    # ... 解析文档 (保持不变)
    
    # ✅ Step 2: 创建 chunks 时传递 user_id
    await vector_store.add_chunks(
        chunks=chunks,
        project_id=project_id,
        resource_id=document_id,
        resource_type="document",
        user_id=user_id,  # ✅ 新增
    )
    
    # ✅ Step 3: 更新 document 时也设置 user_id (如果需要)
    document.user_id = user_id
    await document_repo.update(document)
```

---

## 2. Output Generation (Mindmap)

### 文件路径

找到 mindmap 生成文件，可能是以下位置之一：
- `app/backend/src/research_agent/application/use_cases/outputs/generate_mindmap.py`
- `app/backend/src/research_agent/domain/agents/mindmap_agent.py`

### 修改 1: 生成函数

**找到方法**: 搜索 `async def generate_mindmap` 或 `async def generate`

**当前代码模式**:
```python
async def generate_mindmap(
    project_id: UUID,
    document_ids: list[UUID],
    session: AsyncSession,
) -> Output:
    # ... 生成 mindmap
    output = await output_repo.create(
        Output(
            project_id=project_id,
            output_type="mindmap",
            data=mindmap_data,
        )
    )
    return output
```

**修改为**:
```python
async def generate_mindmap(
    project_id: UUID,
    document_ids: list[UUID],
    session: AsyncSession,
    user_id: str | None = None,  # ✅ 新增参数 (从 API 层传入)
) -> Output:
    # ✅ 如果没有传入 user_id，从 project 获取
    if user_id is None:
        from research_agent.infrastructure.database.repositories.sqlalchemy_project_repo import (
            SQLAlchemyProjectRepository,
        )
        project_repo = SQLAlchemyProjectRepository(session)
        project = await project_repo.find_by_id(project_id)
        user_id = project.user_id if project else None
    
    # ... 生成 mindmap (保持不变)
    
    # ✅ 创建 output 时传递 user_id
    output = await output_repo.create(
        Output(
            project_id=project_id,
            output_type="mindmap",
            data=mindmap_data,
        ),
        user_id=user_id,  # ✅ 新增
    )
    return output
```

---

## 3. Output Generation (Summary)

### 文件路径

找到 summary 生成文件，可能是以下位置之一：
- `app/backend/src/research_agent/application/use_cases/outputs/generate_summary.py`
- `app/backend/src/research_agent/domain/agents/summary_agent.py`

### 修改

与 mindmap 相同的模式：

```python
async def generate_summary(
    project_id: UUID,
    document_ids: list[UUID],
    session: AsyncSession,
    user_id: str | None = None,  # ✅ 新增参数
) -> Output:
    # ✅ 如果没有传入 user_id，从 project 获取
    if user_id is None:
        project_repo = SQLAlchemyProjectRepository(session)
        project = await project_repo.find_by_id(project_id)
        user_id = project.user_id if project else None
    
    # ... 生成 summary
    
    output = await output_repo.create(
        Output(...),
        user_id=user_id,  # ✅ 新增
    )
    return output
```

---

## 4. Chat Service

### 文件路径

找到 chat 服务文件，可能是以下位置之一：
- `app/backend/src/research_agent/application/use_cases/chat/stream_chat.py`
- `app/backend/src/research_agent/application/use_cases/chat/chat_service.py`

### 修改 1: 流式响应函数

**找到方法**: 搜索 `async def stream_response` 或 `async def stream_chat`

**当前代码模式**:
```python
async def stream_response(
    project_id: UUID,
    message: str,
    session: AsyncSession,
):
    # ... 保存用户消息
    await chat_repo.save_message(user_message)
    
    # ... 生成 AI 响应
    
    # ... 保存 AI 消息
    await chat_repo.save_message(ai_message)
```

**修改为**:
```python
async def stream_response(
    project_id: UUID,
    message: str,
    session: AsyncSession,
    user_id: str | None = None,  # ✅ 新增参数
):
    # ✅ 保存用户消息时传递 user_id
    await chat_repo.save_message(
        user_message,
        user_id=user_id,  # ✅ 新增
    )
    
    # ... 生成 AI 响应 (保持不变)
    
    # ✅ 保存 AI 消息时传递 user_id
    await chat_repo.save_message(
        ai_message,
        user_id=user_id,  # ✅ 新增
    )
```

---

## 5. URL Extractor

### 文件路径

找到 URL 提取服务，可能是以下位置之一：
- `app/backend/src/research_agent/application/use_cases/url/extract_url.py`
- `app/backend/src/research_agent/infrastructure/url/extractor.py`

### 修改

```python
async def extract_url(
    url: str,
    project_id: UUID,
    session: AsyncSession,
    user_id: str | None = None,  # ✅ 新增参数
) -> UrlContent:
    # ... 提取内容
    
    # ✅ 创建 url_content 时设置 user_id
    url_content = UrlContentModel(
        url=url,
        project_id=project_id,
        user_id=user_id,  # ✅ 新增
        # ... 其他字段
    )
    session.add(url_content)
    
    # ✅ 创建 chunks 时传递 user_id
    await vector_store.add_chunks(
        chunks=chunks,
        project_id=project_id,
        resource_id=url_content.id,
        resource_type="video" if is_video else "web_page",
        user_id=user_id,  # ✅ 新增
    )
    
    return url_content
```

---

## 6. Task Queue Worker

### 文件路径

如果使用任务队列（如 Celery、asyncio tasks），找到 worker 文件。

### 修改

确保任务 payload 中包含 `user_id`，或从 `project_id` 获取：

```python
async def process_task(task: TaskQueueModel):
    payload = task.payload
    project_id = payload.get("project_id")
    
    # ✅ 获取 user_id
    project = await project_repo.find_by_id(project_id)
    user_id = project.user_id if project else None
    
    # 根据任务类型分发
    if task.task_type == "process_document":
        await process_document(
            document_id=payload["document_id"],
            project_id=project_id,
            user_id=user_id,  # ✅ 传递 user_id
            session=session,
        )
    elif task.task_type == "generate_mindmap":
        await generate_mindmap(
            project_id=project_id,
            document_ids=payload["document_ids"],
            user_id=user_id,  # ✅ 传递 user_id
            session=session,
        )
```

---

## 检查清单

修改完成后，确保以下后台任务都已更新：

### Document Processing
- [ ] `process_document` 函数
- [ ] Chunk 创建时传递 user_id
- [ ] Document 更新时设置 user_id

### Output Generation
- [ ] `generate_mindmap` 函数
- [ ] `generate_summary` 函数
- [ ] `generate_flashcard` 函数 (如果有)
- [ ] `generate_article` 函数 (如果有)

### Chat Service
- [ ] `stream_response` 函数
- [ ] 保存用户消息时传递 user_id
- [ ] 保存 AI 消息时传递 user_id
- [ ] 保存 chat_memory 时传递 user_id

### URL Extraction
- [ ] `extract_url` 函数
- [ ] 创建 url_content 时设置 user_id
- [ ] 创建 chunks 时传递 user_id

### Task Queue (如果有)
- [ ] Worker 处理函数获取 user_id
- [ ] 传递 user_id 到具体任务函数

---

## 验证方法

### 测试文档处理

1. 上传一个文档
2. 等待处理完成
3. 检查数据库：
```sql
SELECT id, user_id FROM documents ORDER BY created_at DESC LIMIT 1;
SELECT id, user_id FROM resource_chunks WHERE resource_type = 'document' ORDER BY created_at DESC LIMIT 5;
```
4. 验证 user_id 与上传用户一致

### 测试 Output 生成

1. 生成一个 mindmap
2. 检查数据库：
```sql
SELECT id, user_id FROM outputs ORDER BY created_at DESC LIMIT 1;
```
3. 验证 user_id 与当前用户一致

### 测试 Chat

1. 发送一条消息
2. 检查数据库：
```sql
SELECT id, role, user_id FROM chat_messages ORDER BY created_at DESC LIMIT 2;
```
3. 验证 user_id 与当前用户一致
