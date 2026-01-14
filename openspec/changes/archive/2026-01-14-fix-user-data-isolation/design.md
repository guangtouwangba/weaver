# Design: User Data Isolation Fix (v2 - Database-Level Isolation)

## 1. Problem Statement

当前只在 `ProjectModel` 有 `user_id` 字段。其他所有资源（documents, chunks, outputs, chat 等）依赖 API 层验证。这存在安全隐患：

1. **API 层遗漏风险** - 开发者忘记添加 `get_verified_project` 依赖
2. **后台任务绕过** - Worker 直接操作数据库，无 API 层保护
3. **查询效率低** - 按用户查询总需要 JOIN projects 表

## 2. Solution: Database-Level User Isolation

### 2.1 核心策略

在所有核心资源表上添加 `user_id` 字段，实现双重隔离：

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: API Layer (FastAPI Dependency)                       │
│  - get_verified_project() 验证项目所有权                         │
│  - 阻止未授权的 HTTP 请求                                        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Database Layer (user_id Column)                       │
│  - 每个资源表都有 user_id 字段                                   │
│  - Repository 层强制按 user_id 过滤                              │
│  - 后台任务、脚本也受保护                                         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 需要修改的数据库表

| 表名 | 优先级 | 修改类型 |
|------|--------|----------|
| `documents` | P0 | 添加 `user_id` 字段 |
| `resource_chunks` | P0 | 添加 `user_id` 字段 |
| `outputs` | P0 | 添加 `user_id` 字段 |
| `canvases` | P0 | 添加 `user_id` 字段 |
| `chat_messages` | P0 | 添加 `user_id` 字段 |
| `chat_memories` | P1 | 添加 `user_id` 字段 |
| `chat_summaries` | P1 | 添加 `user_id` 字段 |
| `highlights` | P2 | 添加 `user_id` 字段 |
| `comments` | P2 | 添加 `user_id` 字段 |

---

## 3. Database Schema Changes

### 3.1 通用 User Isolation 字段定义

每个需要用户隔离的表，添加以下字段：

```python
# 字段定义 (在 models.py 中)
user_id: Mapped[Optional[str]] = mapped_column(
    String(255), 
    nullable=True,  # 第一阶段允许 NULL，便于迁移
    index=True,
    doc="Owner user ID for multi-tenant isolation"
)
```

**字段说明**：
- **类型**: `String(255)` - 与 Supabase Auth 的 user.id 一致
- **nullable**: `True` - 允许历史数据为 NULL（旧数据兼容）
- **index**: `True` - 创建索引，优化查询性能

### 3.2 Migration 脚本模板

为每个表创建独立的 migration 文件：

```python
# alembic/versions/YYYYMMDD_HHMMSS_add_user_id_to_documents.py

"""Add user_id to documents table"""

from alembic import op
import sqlalchemy as sa

revision = 'add_user_id_documents'
down_revision = 'previous_revision'

def upgrade():
    # Step 1: 添加 user_id 列 (允许 NULL)
    op.add_column(
        'documents',
        sa.Column('user_id', sa.String(255), nullable=True)
    )
    
    # Step 2: 创建索引
    op.create_index(
        'idx_documents_user_id',
        'documents',
        ['user_id']
    )
    
    # Step 3: 从关联的 project 回填 user_id
    op.execute("""
        UPDATE documents 
        SET user_id = (
            SELECT user_id 
            FROM projects 
            WHERE projects.id = documents.project_id
        )
        WHERE user_id IS NULL
    """)

def downgrade():
    op.drop_index('idx_documents_user_id', 'documents')
    op.drop_column('documents', 'user_id')
```

---

## 4. Model Changes (Detailed)

### 4.1 DocumentModel

**文件**: `app/backend/src/research_agent/infrastructure/database/models.py`

**修改位置**: `DocumentModel` 类内，在 `project_id` 字段后添加

```python
class DocumentModel(Base):
    """Document ORM model."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(...)
    project_id: Mapped[UUID] = mapped_column(...)
    
    # ✅ 新增: 用户隔离字段
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    filename: Mapped[str] = mapped_column(...)
    # ... 其他字段保持不变
```

### 4.2 ResourceChunkModel

**修改位置**: `ResourceChunkModel` 类内，在 `project_id` 字段后添加

```python
class ResourceChunkModel(Base):
    """Unified resource chunk ORM model."""

    __tablename__ = "resource_chunks"

    id: Mapped[UUID] = mapped_column(...)
    resource_id: Mapped[UUID] = mapped_column(...)
    resource_type: Mapped[str] = mapped_column(...)
    project_id: Mapped[UUID] = mapped_column(...)
    
    # ✅ 新增: 用户隔离字段
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    chunk_index: Mapped[int] = mapped_column(...)
    # ... 其他字段保持不变
```

### 4.3 CanvasModel

**修改位置**: `CanvasModel` 类内，在 `project_id` 字段后添加

```python
class CanvasModel(Base):
    """Canvas ORM model."""

    __tablename__ = "canvases"

    id: Mapped[UUID] = mapped_column(...)
    project_id: Mapped[UUID] = mapped_column(...)
    
    # ✅ 新增: 用户隔离字段
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    data: Mapped[Dict[str, Any]] = mapped_column(...)
    # ... 其他字段保持不变
```

### 4.4 ChatMessageModel

**修改位置**: `ChatMessageModel` 类内，在 `project_id` 字段后添加

```python
class ChatMessageModel(Base):
    """Chat message ORM model."""

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(...)
    project_id: Mapped[UUID] = mapped_column(...)
    
    # ✅ 新增: 用户隔离字段
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    role: Mapped[str] = mapped_column(...)
    # ... 其他字段保持不变
```

### 4.5 ChatMemoryModel

**修改位置**: `ChatMemoryModel` 类内，在 `project_id` 字段后添加

```python
class ChatMemoryModel(Base):
    """Chat memory ORM model."""

    __tablename__ = "chat_memories"

    id: Mapped[UUID] = mapped_column(...)
    project_id: Mapped[UUID] = mapped_column(...)
    
    # ✅ 新增: 用户隔离字段
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    content: Mapped[str] = mapped_column(...)
    # ... 其他字段保持不变
```

### 4.6 ChatSummaryModel

**修改位置**: `ChatSummaryModel` 类内，在 `project_id` 字段后添加

```python
class ChatSummaryModel(Base):
    """Chat summary ORM model."""

    __tablename__ = "chat_summaries"

    id: Mapped[UUID] = mapped_column(...)
    project_id: Mapped[UUID] = mapped_column(...)
    
    # ✅ 新增: 用户隔离字段
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    summary: Mapped[str] = mapped_column(...)
    # ... 其他字段保持不变
```

### 4.7 OutputModel

**修改位置**: `OutputModel` 类内，在 `project_id` 字段后添加

```python
class OutputModel(Base):
    """Output ORM model."""

    __tablename__ = "outputs"

    id: Mapped[UUID] = mapped_column(...)
    project_id: Mapped[UUID] = mapped_column(...)
    
    # ✅ 新增: 用户隔离字段
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    output_type: Mapped[str] = mapped_column(...)
    # ... 其他字段保持不变
```

### 4.8 HighlightModel

**修改位置**: `HighlightModel` 类内，在 `document_id` 字段后添加

```python
class HighlightModel(Base):
    """Highlight ORM model."""

    __tablename__ = "highlights"

    id: Mapped[UUID] = mapped_column(...)
    document_id: Mapped[UUID] = mapped_column(...)
    
    # ✅ 新增: 用户隔离字段
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    page_number: Mapped[int] = mapped_column(...)
    # ... 其他字段保持不变
```

### 4.9 CommentModel

**修改位置**: `CommentModel` 类内，在 `document_id` 字段后添加

```python
class CommentModel(Base):
    """Comment ORM model."""

    __tablename__ = "comments"

    id: Mapped[UUID] = mapped_column(...)
    document_id: Mapped[UUID] = mapped_column(...)
    
    # ✅ 新增: 用户隔离字段
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    parent_id: Mapped[Optional[UUID]] = mapped_column(...)
    # ... 其他字段保持不变
```

---

## 5. Repository Layer Changes

### 5.1 修改原则

所有 Repository 的 **查询方法** 应该接受 `user_id` 参数，并在查询中使用：

```python
# ❌ 旧模式 (不安全)
async def find_by_project_id(self, project_id: UUID) -> list[Document]:
    query = select(DocumentModel).where(
        DocumentModel.project_id == project_id
    )
    ...

# ✅ 新模式 (安全)
async def find_by_project_id(
    self, 
    project_id: UUID, 
    user_id: str | None = None
) -> list[Document]:
    query = select(DocumentModel).where(
        DocumentModel.project_id == project_id
    )
    # 如果提供了 user_id，添加过滤条件
    if user_id:
        query = query.where(DocumentModel.user_id == user_id)
    ...
```

### 5.2 修改所有 Repository 的创建方法

创建资源时，必须设置 `user_id`：

```python
# ❌ 旧模式
async def create(self, document: Document) -> Document:
    model = DocumentModel(
        id=document.id,
        project_id=document.project_id,
        filename=document.filename,
        ...
    )
    ...

# ✅ 新模式
async def create(self, document: Document, user_id: str | None = None) -> Document:
    model = DocumentModel(
        id=document.id,
        project_id=document.project_id,
        user_id=user_id,  # ✅ 设置 user_id
        filename=document.filename,
        ...
    )
    ...
```

### 5.3 需要修改的 Repository 文件

| 文件路径 | 修改内容 |
|---------|---------|
| `infrastructure/database/repositories/sqlalchemy_document_repo.py` | 添加 user_id 参数 |
| `infrastructure/vector_store/pg_vector.py` | 添加 user_id 到 chunk 创建 |
| `infrastructure/database/repositories/sqlalchemy_canvas_repo.py` | 添加 user_id 参数 |
| `infrastructure/database/repositories/sqlalchemy_output_repo.py` | 添加 user_id 参数 |
| `infrastructure/database/repositories/sqlalchemy_chat_repo.py` | 添加 user_id 到消息/记忆创建 |

---

## 6. API Layer Changes

### 6.1 修改原则

所有 API endpoint 在调用 Repository 时，传递 `user_id`：

```python
# ❌ 旧模式
@router.get("/projects/{project_id}/documents")
async def list_documents(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
    _: Project = Depends(get_verified_project),
):
    repo = DocumentRepository(session)
    documents = await repo.find_by_project_id(project_id)
    return documents

# ✅ 新模式
@router.get("/projects/{project_id}/documents")
async def list_documents(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_optional_user),
    _: Project = Depends(get_verified_project),
):
    repo = DocumentRepository(session)
    user_id = user.user_id if user else None
    documents = await repo.find_by_project_id(project_id, user_id=user_id)
    return documents
```

### 6.2 需要修改的 API 文件

| 文件路径 | 修改内容 |
|---------|---------|
| `api/v1/documents.py` | 传递 user_id 到 repo |
| `api/v1/chat.py` | 传递 user_id 到 chat service |
| `api/v1/outputs.py` | 传递 user_id 到 output repo |
| `api/v1/canvas.py` | 传递 user_id 到 canvas repo |
| `api/v1/url.py` | 传递 user_id 到 url_content 创建 |

---

## 7. Background Task Changes

### 7.1 修改原则

后台任务（Worker、Celery task 等）在处理资源时，必须从 payload 或 project 获取 user_id：

```python
# document_processor.py 中的文档处理

async def process_document(document_id: UUID, project_id: UUID):
    # 1. 获取 project 以得到 user_id
    project = await project_repo.find_by_id(project_id)
    user_id = project.user_id if project else None
    
    # 2. 创建 chunks 时设置 user_id
    for chunk in chunks:
        await chunk_repo.create(
            chunk,
            user_id=user_id,  # ✅ 传递 user_id
            project_id=project_id,
        )
```

### 7.2 需要修改的后台任务文件

| 文件路径 | 修改内容 |
|---------|---------|
| `application/use_cases/documents/process_document.py` | 传递 user_id 到 chunk 创建 |
| `application/use_cases/outputs/generate_mindmap.py` | 传递 user_id 到 output 创建 |
| `application/use_cases/outputs/generate_summary.py` | 传递 user_id 到 output 创建 |
| `application/use_cases/chat/stream_chat.py` | 传递 user_id 到消息创建 |

---

## 8. Verification Plan

### 8.1 单元测试

为每个 Repository 添加 user_id 过滤测试：

```python
async def test_document_repo_filters_by_user_id():
    # 创建两个用户的文档
    doc_a = await repo.create(doc, user_id="user_a")
    doc_b = await repo.create(doc, user_id="user_b")
    
    # 查询时只返回自己的文档
    result = await repo.find_by_project_id(project_id, user_id="user_a")
    assert len(result) == 1
    assert result[0].user_id == "user_a"
```

### 8.2 集成测试

使用两个不同的用户账号测试：

1. User A 创建项目和文档
2. User B 尝试访问 User A 的资源
3. 验证返回 403 Forbidden

### 8.3 数据库验证

Migration 后验证数据完整性：

```sql
-- 验证所有文档都有 user_id
SELECT COUNT(*) FROM documents WHERE user_id IS NULL;

-- 验证 user_id 与 project.user_id 一致
SELECT d.id, d.user_id AS doc_user, p.user_id AS proj_user
FROM documents d
JOIN projects p ON d.project_id = p.id
WHERE d.user_id != p.user_id OR (d.user_id IS NULL AND p.user_id IS NOT NULL);
```

---

## 9. Rollback Plan

如果需要回滚：

1. **不删除 user_id 列** - 保留字段，只是停止使用
2. **Repository 改回旧模式** - 移除 user_id 参数
3. **API 层保持 get_verified_project** - 仍然依赖项目级验证

---

## 10. Trade-offs

### Pros
- ✅ 数据库层强制隔离，防止 API 层遗漏
- ✅ 查询效率提升，无需 JOIN projects
- ✅ 调试简单，直接看资源归属
- ✅ 支持未来的跨项目查询（如"用户的所有文档"）

### Cons
- ⚠️ 数据冗余（user_id 在 project 和资源表都存储）
- ⚠️ 需要保持 user_id 同步（项目转移时）
- ⚠️ Migration 需要回填大量数据
