# Spec: Repository Layer User Isolation

## ADDED Requirements

### Requirement: Update Repository Methods

The system SHALL support `user_id` parameter in all Repository create and query methods.

#### Scenario: Verify Repository supports user_id
- **WHEN** a repository method is called with `user_id`
- **THEN** it SHALL filter or save the data using that `user_id`

---

## 1. Document Repository

### 文件路径

`app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_document_repo.py`

### 修改 1: 创建方法

**找到方法**: 搜索 `async def create` 或 `async def add`

**修改签名** (添加 user_id 参数):

```python
# 旧签名
async def create(self, document: Document) -> Document:

# 新签名
async def create(self, document: Document, user_id: str | None = None) -> Document:
```

**修改方法体** (在创建 DocumentModel 时添加 user_id):

```python
# 找到创建 DocumentModel 的代码，添加 user_id
model = DocumentModel(
    id=document.id,
    project_id=document.project_id,
    user_id=user_id,  # ✅ 新增这行
    filename=document.filename,
    original_filename=document.original_filename,
    # ... 其他字段保持不变
)
```

### 修改 2: 查询方法

**找到方法**: 搜索 `async def find_by_project_id` 或类似的查询方法

**修改签名**:

```python
# 旧签名
async def find_by_project_id(self, project_id: UUID) -> list[Document]:

# 新签名
async def find_by_project_id(
    self, 
    project_id: UUID,
    user_id: str | None = None,
) -> list[Document]:
```

**修改方法体** (添加 user_id 过滤):

```python
async def find_by_project_id(
    self, 
    project_id: UUID,
    user_id: str | None = None,
) -> list[Document]:
    query = select(DocumentModel).where(
        DocumentModel.project_id == project_id
    )
    
    # ✅ 新增: 添加 user_id 过滤
    if user_id:
        query = query.where(DocumentModel.user_id == user_id)
    
    result = await self.session.execute(query)
    models = result.scalars().all()
    return [self._to_entity(m) for m in models]
```

### 修改 3: Entity 转换方法

**找到方法**: 搜索 `def _to_entity` 或 `def _model_to_entity`

**修改** (添加 user_id 映射):

```python
def _to_entity(self, model: DocumentModel) -> Document:
    return Document(
        id=model.id,
        project_id=model.project_id,
        user_id=model.user_id,  # ✅ 新增这行
        filename=model.filename,
        # ... 其他字段保持不变
    )
```

---

## 2. PgVector Store (ResourceChunk Repository)

### 文件路径

`app/backend/src/research_agent/infrastructure/vector_store/pg_vector.py`

### 修改 1: add_chunks 方法

**找到方法**: 搜索 `async def add_chunks` 或 `async def store_chunks`

**修改签名**:

```python
# 旧签名
async def add_chunks(
    self,
    chunks: list[ResourceChunk],
    project_id: UUID,
    resource_id: UUID,
    resource_type: str,
) -> None:

# 新签名
async def add_chunks(
    self,
    chunks: list[ResourceChunk],
    project_id: UUID,
    resource_id: UUID,
    resource_type: str,
    user_id: str | None = None,  # ✅ 新增参数
) -> None:
```

**修改方法体** (在创建 ResourceChunkModel 时添加 user_id):

```python
# 找到创建 ResourceChunkModel 的代码，添加 user_id
for i, chunk in enumerate(chunks):
    model = ResourceChunkModel(
        id=chunk.id or uuid4(),
        resource_id=resource_id,
        resource_type=resource_type,
        project_id=project_id,
        user_id=user_id,  # ✅ 新增这行
        chunk_index=i,
        content=chunk.content,
        embedding=chunk.embedding,
        chunk_metadata=chunk.metadata or {},
    )
    self.session.add(model)
```

### 修改 2: 查询方法

**找到方法**: 搜索 `async def search` 或 `async def similarity_search`

**修改签名** (添加 user_id 参数):

```python
# 旧签名
async def search(
    self,
    query_embedding: list[float],
    project_id: UUID,
    limit: int = 10,
) -> list[ResourceChunk]:

# 新签名
async def search(
    self,
    query_embedding: list[float],
    project_id: UUID,
    limit: int = 10,
    user_id: str | None = None,  # ✅ 新增参数
) -> list[ResourceChunk]:
```

**修改方法体** (添加 user_id 过滤):

```python
async def search(
    self,
    query_embedding: list[float],
    project_id: UUID,
    limit: int = 10,
    user_id: str | None = None,
) -> list[ResourceChunk]:
    # 构建查询
    query = select(ResourceChunkModel).where(
        ResourceChunkModel.project_id == project_id
    )
    
    # ✅ 新增: 添加 user_id 过滤
    if user_id:
        query = query.where(ResourceChunkModel.user_id == user_id)
    
    # ... 其他查询逻辑 (排序、限制等)
```

---

## 3. Canvas Repository

### 文件路径

`app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_canvas_repo.py`

### 修改 1: 创建/保存方法

**找到方法**: 搜索 `async def save` 或 `async def create` 或 `async def upsert`

**修改签名**:

```python
# 旧签名
async def save(self, canvas: Canvas) -> Canvas:

# 新签名
async def save(self, canvas: Canvas, user_id: str | None = None) -> Canvas:
```

**修改方法体**:

```python
async def save(self, canvas: Canvas, user_id: str | None = None) -> Canvas:
    # 检查是否存在
    existing = await self.find_by_project_id(canvas.project_id)
    
    if existing:
        # 更新现有记录
        existing.data = canvas.data
        existing.user_id = user_id or existing.user_id  # ✅ 更新 user_id
        # ...
    else:
        # 创建新记录
        model = CanvasModel(
            id=canvas.id,
            project_id=canvas.project_id,
            user_id=user_id,  # ✅ 新增这行
            data=canvas.data,
        )
        self.session.add(model)
```

---

## 4. Output Repository

### 文件路径

`app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_output_repo.py`

### 修改 1: 创建方法

**找到方法**: 搜索 `async def create`

**修改签名**:

```python
# 旧签名
async def create(self, output: Output) -> Output:

# 新签名
async def create(self, output: Output, user_id: str | None = None) -> Output:
```

**修改方法体**:

```python
async def create(self, output: Output, user_id: str | None = None) -> Output:
    model = OutputModel(
        id=output.id or uuid4(),
        project_id=output.project_id,
        user_id=user_id,  # ✅ 新增这行
        output_type=output.output_type,
        source_ids=output.source_ids,
        status=output.status,
        title=output.title,
        data=output.data,
    )
    self.session.add(model)
    await self.session.flush()
    return self._to_entity(model)
```

### 修改 2: 查询方法

**找到方法**: 搜索 `async def find_by_project_id`

**修改签名和方法体**:

```python
async def find_by_project_id(
    self, 
    project_id: UUID,
    user_id: str | None = None,  # ✅ 新增参数
) -> list[Output]:
    query = select(OutputModel).where(
        OutputModel.project_id == project_id
    )
    
    # ✅ 新增: 添加 user_id 过滤
    if user_id:
        query = query.where(OutputModel.user_id == user_id)
    
    result = await self.session.execute(query)
    models = result.scalars().all()
    return [self._to_entity(m) for m in models]
```

---

## 5. Chat Repository

### 文件路径

找到处理 `ChatMessageModel` 的文件 (可能是 `sqlalchemy_chat_repo.py` 或在 use_case 中)

### 修改 1: 保存消息方法

**找到方法**: 搜索 `async def save_message` 或 `async def add_message`

**修改签名**:

```python
# 旧签名
async def save_message(self, message: ChatMessage) -> ChatMessage:

# 新签名
async def save_message(
    self, 
    message: ChatMessage,
    user_id: str | None = None,
) -> ChatMessage:
```

**修改方法体**:

```python
async def save_message(
    self, 
    message: ChatMessage,
    user_id: str | None = None,
) -> ChatMessage:
    model = ChatMessageModel(
        id=message.id or uuid4(),
        project_id=message.project_id,
        user_id=user_id,  # ✅ 新增这行
        role=message.role,
        content=message.content,
        sources=message.sources,
        context_refs=message.context_refs,
    )
    self.session.add(model)
    await self.session.flush()
    return self._to_entity(model)
```

### 修改 2: 查询消息方法

**找到方法**: 搜索 `async def get_history` 或 `async def find_by_project_id`

**修改签名和方法体**:

```python
async def get_history(
    self, 
    project_id: UUID,
    user_id: str | None = None,  # ✅ 新增参数
    limit: int = 50,
) -> list[ChatMessage]:
    query = select(ChatMessageModel).where(
        ChatMessageModel.project_id == project_id
    )
    
    # ✅ 新增: 添加 user_id 过滤
    if user_id:
        query = query.where(ChatMessageModel.user_id == user_id)
    
    query = query.order_by(ChatMessageModel.created_at.desc()).limit(limit)
    
    result = await self.session.execute(query)
    models = result.scalars().all()
    return [self._to_entity(m) for m in models]
```

---

## 验证方法

修改完成后，运行以下命令检查语法：

```bash
cd app/backend
python -c "
from research_agent.infrastructure.database.repositories.sqlalchemy_document_repo import *
from research_agent.infrastructure.vector_store.pg_vector import *
print('Repositories imported successfully')
"
```

如果没有报错，说明修改正确。
