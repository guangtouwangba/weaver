# Design Document: Qdrant Chunk Write

## Overview

当 `VECTOR_STORE_PROVIDER=qdrant` 时，将 chunk embeddings 写入 Qdrant，metadata 写入 PostgreSQL。

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Upload Flow                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  API Endpoint (documents.py)                                 │
│       │                                                      │
│       ▼                                                      │
│  get_chunk_repository(session)  ◄── 新增工厂函数             │
│       │                                                      │
│       ├── VECTOR_STORE_PROVIDER=pgvector                     │
│       │       └── SQLAlchemyChunkRepository                  │
│       │               └── PostgreSQL (embedding + metadata)  │
│       │                                                      │
│       └── VECTOR_STORE_PROVIDER=qdrant                       │
│               └── QdrantChunkRepository  ◄── 新增            │
│                       ├── Qdrant (embedding only)            │
│                       └── PostgreSQL (metadata only)         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. QdrantChunkRepository (新增)

**文件**: `app/backend/src/research_agent/infrastructure/database/repositories/qdrant_chunk_repo.py`

```python
class QdrantChunkRepository(ChunkRepository):
    """Qdrant + PostgreSQL hybrid chunk repository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._qdrant_store = QdrantVectorStore()
    
    async def save_batch(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        # 1. 确保 Qdrant collection 存在
        # 2. 遍历 chunks，调用 _qdrant_store.upsert() 存入 Qdrant
        # 3. 将 chunks 存入 PostgreSQL（embedding 设为 None）
        pass
    
    async def find_by_document(self, document_id: UUID) -> List[DocumentChunk]:
        # 从 PostgreSQL 查询（与 SQLAlchemy 实现相同）
        pass
    
    async def delete_by_document(self, document_id: UUID) -> int:
        # 1. 调用 _qdrant_store.delete_by_document() 删除 Qdrant 数据
        # 2. 从 PostgreSQL 删除
        pass
```

### 2. get_chunk_repository 工厂函数 (新增)

**文件**: `app/backend/src/research_agent/infrastructure/database/repositories/chunk_repo_factory.py`

```python
def get_chunk_repository(session: AsyncSession) -> ChunkRepository:
    settings = get_settings()
    
    if settings.vector_store_provider == "qdrant":
        from .qdrant_chunk_repo import QdrantChunkRepository
        return QdrantChunkRepository(session)
    else:
        from .sqlalchemy_chunk_repo import SQLAlchemyChunkRepository
        return SQLAlchemyChunkRepository(session)
```

### 3. 修改 API 端点

**文件**: `app/backend/src/research_agent/api/v1/documents.py`

将所有 `SQLAlchemyChunkRepository(session)` 替换为 `get_chunk_repository(session)`

## Data Flow

### 写入流程 (VECTOR_STORE_PROVIDER=qdrant)

```
1. 用户上传文档
2. PDF 解析 → 分块 → 生成 embedding
3. QdrantChunkRepository.save_batch(chunks)
   ├── 3.1 ensure_collection_exists() - 确保 Qdrant collection 存在
   ├── 3.2 for chunk in chunks:
   │       qdrant_store.upsert(chunk_id, document_id, project_id, content, embedding, page_number)
   └── 3.3 PostgreSQL: INSERT chunks (embedding=NULL)
```

### 删除流程 (VECTOR_STORE_PROVIDER=qdrant)

```
1. 用户删除文档
2. QdrantChunkRepository.delete_by_document(document_id)
   ├── 2.1 qdrant_store.delete_by_document(document_id)
   └── 2.2 PostgreSQL: DELETE FROM document_chunks WHERE document_id=?
```

## Error Handling

- Qdrant 写入失败时，抛出异常，不继续写入 PostgreSQL
- Qdrant 删除失败时，记录日志，继续删除 PostgreSQL 数据（最终一致性）

## Testing Strategy

1. 单元测试：Mock Qdrant client，验证调用参数
2. 集成测试：启动 Qdrant Docker，验证端到端流程
