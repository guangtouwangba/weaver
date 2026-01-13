# Implementation Plan: Unified Resource Chunks

## Overview

统一所有资源类型的 chunk 存储架构，实现跨资源类型的语义检索。

## Tasks

- [x] 1. 创建 ResourceChunk 实体
  - 文件: `app/backend/src/research_agent/domain/entities/resource_chunk.py`
  - [x] 1.1 创建 ResourceChunk dataclass
  - [x] 1.2 包含字段: id, resource_id, resource_type, project_id, chunk_index, content, embedding, metadata
  - [x] 1.3 添加 helper 方法: has_embedding, set_embedding
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. 创建 ResourceChunkModel (PostgreSQL)
  - 文件: `app/backend/src/research_agent/infrastructure/database/models.py`
  - [x] 2.1 添加 ResourceChunkModel 类
  - [x] 2.2 字段: id, resource_id, resource_type, project_id, chunk_index, content, embedding, metadata, created_at
  - [x] 2.3 添加索引: resource_id, project_id, resource_type
  - _Requirements: 1.1, 5.1_

- [x] 3. 创建数据库迁移
  - 文件: `app/backend/alembic/versions/20260113_000001_create_resource_chunks_table.py`
  - [x] 3.1 创建 resource_chunks 表
  - [x] 3.2 添加 content_tsvector 列 (用于 hybrid search)
  - [x] 3.3 创建 tsvector 自动更新 trigger
  - [x] 3.4 创建向量索引 (HNSW for pgvector)
  - [x] 3.5 创建 GIN 索引 (for tsvector)
  - [ ] 3.6 删除 document_chunks 表 (breaking change) - 保留用于向后兼容
  - _Requirements: 5.1_

- [x] 4. 更新 ChunkRepository 接口
  - 文件: `app/backend/src/research_agent/domain/repositories/chunk_repo.py`
  - [x] 4.1 更新方法签名使用 ResourceChunk
  - [x] 4.2 添加 search 方法到接口
  - [x] 4.3 添加 resource_type 过滤参数
  - _Requirements: 2.1, 2.2_

- [x] 5. 实现 SQLAlchemyChunkRepository
  - 文件: `app/backend/src/research_agent/infrastructure/database/repositories/sqlalchemy_chunk_repo.py`
  - [x] 5.1 更新 save_batch 使用 ResourceChunk
  - [x] 5.2 更新 find_by_resource (原 find_by_document)
  - [x] 5.3 更新 delete_by_resource (原 delete_by_document)
  - [x] 5.4 实现 search 方法 (pgvector)
  - [x] 5.5 实现 hybrid_search 方法 (RRF fusion)
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 6. 实现 QdrantChunkRepository
  - 文件: `app/backend/src/research_agent/infrastructure/database/repositories/qdrant_chunk_repo.py`
  - [x] 6.1 更新 save_batch: 写入 Qdrant + PostgreSQL
  - [x] 6.2 更新 Qdrant payload schema: 添加 resource_type, title, platform
  - [x] 6.3 实现 search 方法: 支持 resource_type 过滤
  - [x] 6.4 更新 delete_by_resource
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 7. 更新 Qdrant collection 初始化
  - 文件: `app/backend/src/research_agent/infrastructure/vector_store/qdrant.py`
  - [x] 7.1 添加 resource_type payload index
  - [x] 7.2 添加 upsert_resource_chunk 方法
  - [x] 7.3 添加 search_resource_chunks 方法
  - [x] 7.4 添加 delete_by_resource 方法
  - _Requirements: 5.3_

- [x] 8. 创建 ResourceChunker 服务
  - 文件: `app/backend/src/research_agent/domain/services/resource_chunker.py`
  - [x] 8.1 创建 ResourceChunker 类
  - [x] 8.2 实现 chunk_resource(resource: Resource) 方法
  - [x] 8.3 实现 _chunk_document: 按页/段落分块，保留 page_number
  - [x] 8.4 实现 _chunk_media: 按时间窗口分块，保留 start_time/end_time
  - [x] 8.5 实现 _chunk_webpage: 按段落分块
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 9. 更新 Document 上传流程
  - 文件: `app/backend/src/research_agent/worker/tasks/document_processor.py`
  - [x] 9.1 使用 ResourceChunk 替代 DocumentChunk
  - [x] 9.2 添加 metadata (title, platform, page_number)
  - [x] 9.3 使用 get_chunk_repository 保存 chunks
  - _Requirements: 3.1, 3.2_

- [x] 10. 添加 URL Content chunking
  - 文件: `app/backend/src/research_agent/worker/tasks/url_processor.py`
  - [x] 10.1 URL 内容提取后调用 chunking
  - [x] 10.2 生成 embedding
  - [x] 10.3 保存到 ChunkRepository
  - [x] 10.4 支持 video/audio 时间戳分块
  - _Requirements: 3.1, 3.3_

- [x] 11. 更新检索服务
  - 文件: `app/backend/src/research_agent/domain/services/retrieval_service.py`
  - [x] 11.1 保留原有 RetrievalService 兼容性
  - [x] 11.2 添加 UnifiedRetrievalService 使用 ChunkRepository
  - [x] 11.3 支持 resource_type 过滤
  - [x] 11.4 添加 retrieve_by_types 方法
  - [x] 11.5 添加 format_context 方法
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 12. 更新 Chat 流程 (可选优化)
  - 文件: `app/backend/src/research_agent/application/use_cases/chat/stream_message.py`
  - [ ] 12.1 使用 UnifiedRetrievalService 替代 RetrievalService
  - [ ] 12.2 更新 source 显示包含 resource_type
  - _Requirements: 4.1, 4.2_
  - _Note: 现有 RetrievalService 保持兼容，此任务为可选优化_

- [ ] 13. 清理旧代码 (可选)
  - [ ] 13.1 删除 DocumentChunk 实体 (用 ResourceChunk 替代) - 保留用于向后兼容
  - [ ] 13.2 删除 DocumentChunkModel (用 ResourceChunkModel 替代) - 保留用于向后兼容
  - [ ] 13.3 更新所有 import 语句
  - _Requirements: 1.1_
  - _Note: 保留旧代码用于向后兼容，新代码使用 ResourceChunk_

- [ ] 14. 验证测试
  - [ ] 14.1 上传 PDF，验证 chunks 存储到 resource_chunks 表
  - [ ] 14.2 添加 YouTube URL，验证 transcript chunks 存储正确
  - [ ] 14.3 发送 chat 消息，验证能同时检索 PDF 和 Video 内容
  - [ ] 14.4 验证 source 显示正确的 resource_type
  - _Requirements: 4.1, 4.2, 4.3_

---

## 详细实现步骤

### Task 1: 创建 ResourceChunk 实体

```python
# app/backend/src/research_agent/domain/entities/resource_chunk.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from research_agent.domain.entities.resource import ResourceType


@dataclass
class ResourceChunk:
    """Unified chunk entity for all resource types."""

    id: UUID = field(default_factory=uuid4)
    resource_id: UUID = None          # Parent resource ID
    resource_type: ResourceType = ResourceType.DOCUMENT
    project_id: UUID = None
    chunk_index: int = 0
    content: str = ""
    embedding: Optional[List[float]] = None
    
    # Metadata (type-specific)
    # Common: title, platform
    # Document: page_number
    # Video/Audio: start_time, end_time
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.utcnow)

    def set_embedding(self, embedding: List[float]) -> None:
        """Set the embedding vector."""
        self.embedding = embedding

    @property
    def has_embedding(self) -> bool:
        """Check if chunk has embedding."""
        return self.embedding is not None and len(self.embedding) > 0
    
    @property
    def title(self) -> str:
        """Get resource title from metadata."""
        return self.metadata.get("title", "")
    
    @property
    def platform(self) -> str:
        """Get platform from metadata."""
        return self.metadata.get("platform", "local")
    
    @property
    def page_number(self) -> Optional[int]:
        """Get page number (for documents)."""
        return self.metadata.get("page_number")
    
    @property
    def start_time(self) -> Optional[float]:
        """Get start time in seconds (for video/audio)."""
        return self.metadata.get("start_time")
    
    @property
    def end_time(self) -> Optional[float]:
        """Get end time in seconds (for video/audio)."""
        return self.metadata.get("end_time")
```

---

### Task 2: 创建 ResourceChunkModel

```python
# 添加到 app/backend/src/research_agent/infrastructure/database/models.py

class ResourceChunkModel(Base):
    """Unified chunk model for all resource types."""

    __tablename__ = "resource_chunks"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    resource_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, server_default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

---

### Task 4: 更新 ChunkRepository 接口

```python
# app/backend/src/research_agent/domain/repositories/chunk_repo.py

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from research_agent.domain.entities.resource import ResourceType
from research_agent.domain.entities.resource_chunk import ResourceChunk


@dataclass
class ChunkSearchResult:
    """Search result from chunk repository."""
    chunk_id: UUID
    resource_id: UUID
    resource_type: ResourceType
    content: str
    similarity: float
    metadata: Dict[str, Any]


class ChunkRepository(ABC):
    """Abstract chunk repository interface."""

    @abstractmethod
    async def save_batch(self, chunks: List[ResourceChunk]) -> List[ResourceChunk]:
        """Save multiple chunks."""
        pass

    @abstractmethod
    async def find_by_resource(self, resource_id: UUID) -> List[ResourceChunk]:
        """Find all chunks for a resource."""
        pass

    @abstractmethod
    async def delete_by_resource(self, resource_id: UUID) -> int:
        """Delete all chunks for a resource. Returns count deleted."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        project_id: UUID,
        limit: int = 5,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[UUID] = None,
    ) -> List[ChunkSearchResult]:
        """Search for similar chunks."""
        pass
```

---

### Task 6: 更新 QdrantChunkRepository

```python
# Qdrant payload 更新为:
payload = {
    "chunk_id": str(chunk.id),
    "resource_id": str(chunk.resource_id),
    "resource_type": chunk.resource_type.value,  # "document", "video", etc.
    "project_id": str(chunk.project_id),
    "chunk_index": chunk.chunk_index,
    "content": chunk.content,
    "title": chunk.metadata.get("title", ""),
    "platform": chunk.metadata.get("platform", "local"),
    "page_number": chunk.metadata.get("page_number"),
    "start_time": chunk.metadata.get("start_time"),
    "end_time": chunk.metadata.get("end_time"),
}

# Search 支持 resource_type 过滤:
if resource_type:
    must_conditions.append(
        FieldCondition(
            key="resource_type",
            match=MatchValue(value=resource_type.value),
        )
    )
```

---

### Task 8: ResourceChunker 服务

```python
# app/backend/src/research_agent/domain/services/resource_chunker.py

class ResourceChunker:
    """Unified chunking service for all resource types."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
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
    
    def _chunk_document(self, resource: Resource) -> List[ResourceChunk]:
        """Chunk document content, preserving page numbers."""
        # 使用现有的 ChunkingService 逻辑
        # 返回 ResourceChunk 列表，metadata 包含 page_number
        pass
    
    def _chunk_media(self, resource: Resource) -> List[ResourceChunk]:
        """Chunk video/audio transcript, preserving timestamps."""
        # 按时间窗口分块（如每 60 秒一个 chunk）
        # metadata 包含 start_time, end_time
        pass
    
    def _chunk_webpage(self, resource: Resource) -> List[ResourceChunk]:
        """Chunk webpage content by paragraphs."""
        # 按段落分块
        pass
```

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `domain/entities/resource_chunk.py` | 新增 | ResourceChunk 实体 |
| `domain/entities/chunk.py` | 删除 | 被 resource_chunk.py 替代 |
| `domain/repositories/chunk_repo.py` | 修改 | 更新接口 |
| `domain/services/resource_chunker.py` | 新增 | 统一 chunking 服务 |
| `domain/services/chunking_service.py` | 删除/重构 | 合并到 resource_chunker |
| `infrastructure/database/models.py` | 修改 | 添加 ResourceChunkModel |
| `infrastructure/database/repositories/sqlalchemy_chunk_repo.py` | 修改 | 使用 ResourceChunk |
| `infrastructure/database/repositories/qdrant_chunk_repo.py` | 修改 | 更新 payload schema |
| `infrastructure/vector_store/qdrant.py` | 修改 | 添加 resource_type index |
| `worker/tasks/document_processor.py` | 修改 | 使用 ResourceChunker |
| `worker/tasks/url_processor.py` | 新增/修改 | 添加 URL chunking |
| `application/use_cases/chat/stream_message.py` | 修改 | 统一检索逻辑 |
| `alembic/versions/xxx_create_resource_chunks.py` | 新增 | 数据库迁移 |
