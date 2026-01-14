# Spec: Database Models User Isolation

## ADDED Requirements

### Requirement: Add User ID to Models

The system SHALL include `user_id` field in all ORM models for core resource tables.

#### Scenario: Verify Model has user_id
- **WHEN** an ORM model is inspected
- **THEN** it SHALL have a `user_id` column definition

## 文件路径

`app/backend/src/research_agent/infrastructure/database/models.py`

---

## 修改清单

### 1. DocumentModel

**找到位置**: 搜索 `class DocumentModel(Base):`

**在以下代码后面**:
```python
project_id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
)
```

**添加代码**:
```python
# User ownership for multi-tenant isolation
user_id: Mapped[Optional[str]] = mapped_column(
    String(255), nullable=True, index=True
)
```

---

### 2. ResourceChunkModel

**找到位置**: 搜索 `class ResourceChunkModel(Base):`

**在以下代码后面**:
```python
project_id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
)
```

**添加代码**:
```python
# User ownership for multi-tenant isolation
user_id: Mapped[Optional[str]] = mapped_column(
    String(255), nullable=True, index=True
)
```

---

### 3. CanvasModel

**找到位置**: 搜索 `class CanvasModel(Base):`

**在以下代码后面**:
```python
project_id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("projects.id", ondelete="CASCADE"),
    nullable=False,
    unique=True,
)
```

**添加代码**:
```python
# User ownership for multi-tenant isolation
user_id: Mapped[Optional[str]] = mapped_column(
    String(255), nullable=True, index=True
)
```

---

### 4. ChatMessageModel

**找到位置**: 搜索 `class ChatMessageModel(Base):`

**在以下代码后面**:
```python
project_id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
)
```

**添加代码**:
```python
# User ownership for multi-tenant isolation
user_id: Mapped[Optional[str]] = mapped_column(
    String(255), nullable=True, index=True
)
```

---

### 5. ChatMemoryModel

**找到位置**: 搜索 `class ChatMemoryModel(Base):`

**在以下代码后面**:
```python
project_id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("projects.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
)
```

**添加代码**:
```python
# User ownership for multi-tenant isolation
user_id: Mapped[Optional[str]] = mapped_column(
    String(255), nullable=True, index=True
)
```

---

### 6. ChatSummaryModel

**找到位置**: 搜索 `class ChatSummaryModel(Base):`

**在以下代码后面**:
```python
project_id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("projects.id", ondelete="CASCADE"),
    nullable=False,
    unique=True,  # One summary per project
    index=True,
)
```

**添加代码**:
```python
# User ownership for multi-tenant isolation
user_id: Mapped[Optional[str]] = mapped_column(
    String(255), nullable=True, index=True
)
```

---

### 7. OutputModel

**找到位置**: 搜索 `class OutputModel(Base):`

**在以下代码后面**:
```python
project_id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("projects.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
)
```

**添加代码**:
```python
# User ownership for multi-tenant isolation
user_id: Mapped[Optional[str]] = mapped_column(
    String(255), nullable=True, index=True
)
```

---

### 8. HighlightModel

**找到位置**: 搜索 `class HighlightModel(Base):`

**在以下代码后面**:
```python
document_id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
)
```

**添加代码**:
```python
# User ownership for multi-tenant isolation
user_id: Mapped[Optional[str]] = mapped_column(
    String(255), nullable=True, index=True
)
```

---

### 9. CommentModel

**找到位置**: 搜索 `class CommentModel(Base):`

**在以下代码后面**:
```python
document_id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
)
```

**添加代码**:
```python
# User ownership for multi-tenant isolation
user_id: Mapped[Optional[str]] = mapped_column(
    String(255), nullable=True, index=True
)
```

---

## 验证方法

修改完成后，运行以下命令检查语法：

```bash
cd app/backend
python -c "from research_agent.infrastructure.database.models import *; print('Models imported successfully')"
```

如果没有报错，说明修改正确。
