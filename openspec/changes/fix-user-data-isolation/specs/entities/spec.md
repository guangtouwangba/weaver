# Spec: Domain Entities User Isolation

## 目标

在所有 Domain Entity 类中添加 `user_id` 属性。

---

## 1. Document Entity

### 文件路径

`app/backend/src/research_agent/domain/entities/document.py`

### 修改

**找到方法**: 搜索 `class Document` 或 `@dataclass`

**当前代码模式**:
```python
@dataclass
class Document:
    id: UUID
    project_id: UUID
    filename: str
    original_filename: str
    # ... 其他字段
```

**修改为**:
```python
@dataclass
class Document:
    id: UUID
    project_id: UUID
    user_id: str | None = None  # ✅ 新增
    filename: str = ""
    original_filename: str = ""
    # ... 其他字段
```

**注意**: 新增的字段如果有默认值，应该放在没有默认值的字段后面，或者给所有字段都加上默认值。

---

## 2. ResourceChunk Entity

### 文件路径

`app/backend/src/research_agent/domain/entities/resource_chunk.py`

### 修改

**找到 ResourceChunk 类**:

```python
@dataclass
class ResourceChunk:
    id: UUID | None = None
    resource_id: UUID | None = None
    resource_type: str = ""
    project_id: UUID | None = None
    user_id: str | None = None  # ✅ 新增
    chunk_index: int = 0
    content: str = ""
    # ... 其他字段
```

---

## 3. Canvas Entity

### 文件路径

`app/backend/src/research_agent/domain/entities/canvas.py`

### 修改

**找到 Canvas 类**:

```python
@dataclass
class Canvas:
    id: UUID
    project_id: UUID
    user_id: str | None = None  # ✅ 新增
    data: dict = field(default_factory=dict)
    # ... 其他字段
```

---

## 4. Output Entity

### 文件路径

`app/backend/src/research_agent/domain/entities/output.py`

### 修改

**找到 Output 类**:

```python
@dataclass
class Output:
    id: UUID | None = None
    project_id: UUID | None = None
    user_id: str | None = None  # ✅ 新增
    output_type: str = ""
    source_ids: list[UUID] = field(default_factory=list)
    status: str = "generating"
    # ... 其他字段
```

---

## 5. Chat Entity

### 文件路径

`app/backend/src/research_agent/domain/entities/chat.py`

### 修改

**找到 ChatMessage 类**:

```python
@dataclass
class ChatMessage:
    id: UUID | None = None
    project_id: UUID | None = None
    user_id: str | None = None  # ✅ 新增
    role: str = ""  # "user" or "ai"
    content: str = ""
    # ... 其他字段
```

**如果还有 ChatMemory 类**:

```python
@dataclass
class ChatMemory:
    id: UUID | None = None
    project_id: UUID | None = None
    user_id: str | None = None  # ✅ 新增
    content: str = ""
    # ... 其他字段
```

---

## 验证方法

```bash
cd app/backend
python -c "
from research_agent.domain.entities.document import Document
from research_agent.domain.entities.canvas import Canvas
from research_agent.domain.entities.output import Output
from research_agent.domain.entities.chat import ChatMessage
from research_agent.domain.entities.resource_chunk import ResourceChunk

# 验证新属性存在
doc = Document(id=None, project_id=None, user_id='test_user')
print(f'Document user_id: {doc.user_id}')

print('All entities imported and created successfully')
"
```

如果没有报错，说明修改正确。

---

## 注意事项

### Pydantic vs Dataclass

如果项目使用 Pydantic 而不是 dataclass，修改方式略有不同：

```python
# Pydantic v2 风格
from pydantic import BaseModel

class Document(BaseModel):
    id: UUID
    project_id: UUID
    user_id: str | None = None  # ✅ 新增
    filename: str
    # ...
```

### TypedDict

如果使用 TypedDict：

```python
from typing import TypedDict

class DocumentDict(TypedDict, total=False):
    id: str
    project_id: str
    user_id: str  # ✅ 新增
    filename: str
    # ...
```

### 检查现有代码

在添加 `user_id` 后，搜索代码中所有创建该 Entity 的地方，确保不会因为新增字段导致错误：

```bash
# 搜索创建 Document 的地方
grep -r "Document(" --include="*.py" app/backend/src/

# 搜索创建 Output 的地方
grep -r "Output(" --include="*.py" app/backend/src/
```

如果使用位置参数创建，需要更新为关键字参数，或者调整参数顺序。
