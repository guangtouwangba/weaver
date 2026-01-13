# Design Document: Unified Resource Chunks

## Overview

将所有资源类型（Document、URL Content、Note 等）的 chunk 存储统一到一个架构中，实现：
- 统一的实体模型
- 统一的存储接口
- 统一的检索体验（支持 Vector Search 和 Hybrid Search）

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Resource Sources                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Document │  │  Video   │  │ Article  │  │   Note   │            │
│  │  (PDF)   │  │(YouTube) │  │  (Web)   │  │ (Future) │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
│       │             │             │             │                   │
│       └─────────────┴─────────────┴─────────────┘                   │
│                           │                                          │
│                           ▼                                          │
│              ┌────────────────────────┐                             │
│              │   ResourceChunker      │                             │
│              │   (Unified Chunking)   │                             │
│              └───────────┬────────────┘                             │
│                          │                                          │
│                          ▼                                          │
│              ┌────────────────────────┐                             │
│              │   ResourceChunk[]      │                             │
│              │   (Unified Entity)     │                             │
│              └───────────┬────────────┘                             │
│                          │                                          │
│                          ▼                                          │
│              ┌────────────────────────┐                             │
│              │  ChunkRepository       │                             │
│              │  (Factory Pattern)     │                             │
│              └───────────┬────────────┘                             │
│                          │                                          │
│           ┌──────────────┴──────────────┐                           │
│           ▼                             ▼                           │
│  ┌─────────────────┐          ┌─────────────────┐                  │
│  │ QdrantChunkRepo │          │ PgVectorChunkRepo│                  │
│  │ (Vector Only)   │          │ (Vector+Hybrid)  │                  │
│  └────────┬────────┘          └────────┬────────┘                  │
│           │                            │                            │
│           ▼                            ▼                            │
│  ┌─────────────────┐          ┌─────────────────┐                  │
│  │     Qdrant      │          │   PostgreSQL    │                  │
│  │   Collection    │          │  resource_chunks│                  │
│  │   (embedding)   │          │  (embedding +   │                  │
│  │                 │          │   content_tsvec)│                  │
│  └─────────────────┘          └─────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Query Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Query Flow                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User Query: "视频里讲了什么关于机器学习的内容？"                      │
│       │                                                              │
│       ▼                                                              │
│  ┌────────────────────────┐                                         │
│  │   Embedding Service    │                                         │
│  │   (query → vector)     │                                         │
│  └───────────┬────────────┘                                         │
│              │                                                       │
│              ▼                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │                    VectorStore.search()                     │     │
│  │                    or hybrid_search()                       │     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │  Filters:                                                   │     │
│  │  - project_id (required)                                    │     │
│  │  - resource_type (optional): video, document, web_page      │     │
│  │  - resource_id (optional): specific resource                │     │
│  └───────────┬────────────────────────────────────────────────┘     │
│              │                                                       │
│              ▼                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │                    Search Results                           │     │
│  │  [                                                          │     │
│  │    {chunk_id, resource_id, resource_type: "video",          │     │
│  │     content: "机器学习是...", similarity: 0.92,              │     │
│  │     metadata: {title: "ML Tutorial", start_time: 120}},     │     │
│  │    {chunk_id, resource_id, resource_type: "document",       │     │
│  │     content: "深度学习基础...", similarity: 0.88,            │     │
│  │     metadata: {title: "ML Paper.pdf", page_number: 5}},     │     │
│  │  ]                                                          │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Models

### ResourceChunk Entity

```python
@dataclass
class ResourceChunk:
    """Unified chunk entity for all resource types."""
    
    id: UUID
    resource_id: UUID           # ID of parent resource (document, url_content, etc.)
    resource_type: ResourceType # document, video, audio, web_page, note
    project_id: UUID
    chunk_index: int
    content: str
    embedding: Optional[List[float]] = None
    
    # Metadata (type-specific)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Common metadata fields:
    # - title: str              # Resource title
    # - platform: str           # local, youtube, bilibili, web, etc.
    # - page_number: int        # For documents
    # - start_time: float       # For video/audio (seconds)
    # - end_time: float         # For video/audio (seconds)
    
    created_at: datetime
```

### Qdrant Payload Schema

```json
{
  "chunk_id": "uuid",
  "resource_id": "uuid",
  "resource_type": "video",
  "project_id": "uuid",
  "chunk_index": 0,
  "content": "chunk text content...",
  "title": "Video Title",
  "platform": "youtube",
  "page_number": null,
  "start_time": 120.5,
  "end_time": 180.0
}
```

### PostgreSQL Schema (resource_chunks)

```sql
CREATE TABLE resource_chunks (
    id UUID PRIMARY KEY,
    resource_id UUID NOT NULL,
    resource_type VARCHAR(50) NOT NULL,  -- document, video, audio, web_page, note
    project_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),              -- Only for pgvector mode
    content_tsvector TSVECTOR,           -- For hybrid search (full-text)
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_resource_chunks_resource_id (resource_id),
    INDEX idx_resource_chunks_project_id (project_id),
    INDEX idx_resource_chunks_type (resource_type),
    INDEX idx_resource_chunks_embedding USING hnsw (embedding vector_cosine_ops),
    INDEX idx_resource_chunks_tsvector USING GIN (content_tsvector)
);

-- Trigger to auto-update tsvector on insert/update
CREATE TRIGGER tsvector_update_trigger
    BEFORE INSERT OR UPDATE ON resource_chunks
    FOR EACH ROW EXECUTE FUNCTION
    tsvector_update_trigger(content_tsvector, 'pg_catalog.english', content);
```

## Search Interfaces

### VectorStore Interface (Updated)

```python
@dataclass
class SearchResult:
    """Vector search result with resource metadata."""
    chunk_id: UUID
    resource_id: UUID
    resource_type: ResourceType  # NEW: document, video, web_page, etc.
    content: str
    similarity: float
    metadata: Dict[str, Any]     # NEW: title, platform, page_number, start_time, etc.


class VectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        project_id: UUID,
        limit: int = 5,
        resource_type: Optional[ResourceType] = None,  # NEW: filter by type
        resource_id: Optional[UUID] = None,
    ) -> list[SearchResult]:
        """Vector similarity search."""
        pass

    async def hybrid_search(
        self,
        query_embedding: list[float],
        query_text: str,
        project_id: UUID,
        limit: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        k: int = 20,
        resource_type: Optional[ResourceType] = None,  # NEW: filter by type
        resource_id: Optional[UUID] = None,
    ) -> list[SearchResult]:
        """Hybrid search (vector + keyword)."""
        pass
```

### Hybrid Search Implementation

**pgvector (PostgreSQL)**:
- Vector search: `embedding <=> query_embedding`
- Keyword search: `content_tsvector @@ websearch_to_tsquery(query_text)`
- Fusion: Reciprocal Rank Fusion (RRF)

**Qdrant**:
- Vector search: Native Qdrant vector search
- Keyword search: Qdrant sparse vectors (future) or fallback to vector-only
- Note: Qdrant CE 不支持 BM25，可以用 sparse vectors 或 payload 全文搜索

## Components

### 1. ResourceChunk Entity

**File**: `domain/entities/resource_chunk.py`

替代原有的 `DocumentChunk`，支持所有资源类型。

### 2. ChunkRepository Interface

**File**: `domain/repositories/chunk_repo.py`

```python
class ChunkRepository(ABC):
    @abstractmethod
    async def save_batch(self, chunks: List[ResourceChunk]) -> List[ResourceChunk]:
        pass
    
    @abstractmethod
    async def find_by_resource(self, resource_id: UUID) -> List[ResourceChunk]:
        pass
    
    @abstractmethod
    async def delete_by_resource(self, resource_id: UUID) -> int:
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        project_id: UUID,
        limit: int = 5,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[UUID] = None,
    ) -> List[SearchResult]:
        pass
```

### 3. QdrantChunkRepository

**File**: `infrastructure/database/repositories/qdrant_chunk_repo.py`

- `save_batch`: 写入 Qdrant + PostgreSQL metadata
- `search`: 从 Qdrant 检索，支持 resource_type 过滤
- `delete_by_resource`: 从 Qdrant + PostgreSQL 删除

### 4. ResourceChunker Service

**File**: `domain/services/resource_chunker.py`

```python
class ResourceChunker:
    """Unified chunking service for all resource types."""
    
    def chunk_resource(self, resource: Resource) -> List[ResourceChunk]:
        """Chunk a resource based on its type."""
        if resource.type == ResourceType.DOCUMENT:
            return self._chunk_document(resource)
        elif resource.type in (ResourceType.VIDEO, ResourceType.AUDIO):
            return self._chunk_media(resource)
        elif resource.type == ResourceType.WEB_PAGE:
            return self._chunk_webpage(resource)
        else:
            return self._chunk_generic(resource)
```

### 5. Updated VectorStore Interface

**File**: `infrastructure/vector_store/base.py`

```python
@dataclass
class SearchResult:
    chunk_id: UUID
    resource_id: UUID
    resource_type: ResourceType
    content: str
    similarity: float
    metadata: Dict[str, Any]  # title, platform, page_number, etc.
```

## Migration Strategy

### Breaking Changes (Accepted)

1. 删除 `document_chunks` 表，创建 `resource_chunks` 表
2. 删除 `DocumentChunk` 实体，使用 `ResourceChunk`
3. 更新所有使用 `DocumentChunk` 的代码

### Files to Modify

| File | Change |
|------|--------|
| `domain/entities/chunk.py` | 重命名为 `resource_chunk.py`，更新实体 |
| `domain/repositories/chunk_repo.py` | 更新接口方法签名 |
| `infrastructure/database/models.py` | 添加 `ResourceChunkModel` |
| `infrastructure/database/repositories/sqlalchemy_chunk_repo.py` | 更新实现 |
| `infrastructure/database/repositories/qdrant_chunk_repo.py` | 更新实现 |
| `infrastructure/vector_store/qdrant.py` | 更新 payload schema |
| `domain/services/chunking_service.py` | 重构为 `ResourceChunker` |
| `application/use_cases/document/upload_document.py` | 使用新的 chunking |
| `worker/tasks/document_processor.py` | 使用新的 chunking |
| URL 处理相关代码 | 添加 chunking 和 embedding |

## Error Handling

- Qdrant 写入失败：抛出异常，回滚整个操作
- Qdrant 删除失败：记录日志，继续删除 PostgreSQL（最终一致性）
- 检索失败：返回空结果，记录错误

## Testing Strategy

1. 单元测试：Mock 存储层，验证 chunking 逻辑
2. 集成测试：验证 Document 和 URL Content 都能被检索
3. E2E 测试：上传 PDF + YouTube URL，验证统一检索
