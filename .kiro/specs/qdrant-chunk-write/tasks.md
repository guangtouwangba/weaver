# Implementation Plan: Qdrant Chunk Write

## Overview

实现当 `VECTOR_STORE_PROVIDER=qdrant` 时，chunks 写入 Qdrant 的功能。

## Tasks

- [ ] 1. 创建 QdrantChunkRepository 类
  - 文件: `app/backend/src/research_agent/infrastructure/database/repositories/qdrant_chunk_repo.py`
  - [ ] 1.1 创建文件，添加 imports
  - [ ] 1.2 实现 `__init__` 方法
  - [ ] 1.3 实现 `save_batch` 方法
  - [ ] 1.4 实现 `find_by_document` 方法
  - [ ] 1.5 实现 `delete_by_document` 方法
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. 创建 ChunkRepository 工厂函数
  - 文件: `app/backend/src/research_agent/infrastructure/database/repositories/chunk_repo_factory.py`
  - [ ] 2.1 创建文件
  - [ ] 2.2 实现 `get_chunk_repository(session)` 函数
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 3. 更新 documents.py API 端点
  - 文件: `app/backend/src/research_agent/api/v1/documents.py`
  - [ ] 3.1 添加 import `get_chunk_repository`
  - [ ] 3.2 替换 `upload_document` 函数中的 `SQLAlchemyChunkRepository(session)` 为 `get_chunk_repository(session)`
  - [ ] 3.3 替换 `get_document_chunks` 函数中的 `SQLAlchemyChunkRepository(session)` 为 `get_chunk_repository(session)`
  - [ ] 3.4 替换 `delete_document` 函数中的 `SQLAlchemyChunkRepository(session)` 为 `get_chunk_repository(session)`
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 4. 更新 worker 处理逻辑（如果有）
  - [ ] 4.1 搜索其他使用 `SQLAlchemyChunkRepository` 的地方
  - [ ] 4.2 替换为 `get_chunk_repository(session)`
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 5. 验证测试
  - [ ] 5.1 设置 `VECTOR_STORE_PROVIDER=qdrant`
  - [ ] 5.2 启动 Qdrant (docker-compose)
  - [ ] 5.3 上传文档，验证 Qdrant 中有数据
  - [ ] 5.4 删除文档，验证 Qdrant 中数据被删除
  - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.2_

---

## 详细实现步骤

### Task 1: 创建 QdrantChunkRepository

#### 1.1 创建文件，添加 imports

创建文件 `app/backend/src/research_agent/infrastructure/database/repositories/qdrant_chunk_repo.py`

```python
"""Qdrant implementation of ChunkRepository."""

from typing import List
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.domain.entities.chunk import DocumentChunk
from research_agent.domain.repositories.chunk_repo import ChunkRepository
from research_agent.infrastructure.database.models import DocumentChunkModel
from research_agent.infrastructure.vector_store.qdrant import (
    QdrantVectorStore,
    ensure_collection_exists,
    get_qdrant_client,
)
from research_agent.shared.utils.logger import logger
```

#### 1.2 实现 `__init__` 方法

```python
class QdrantChunkRepository(ChunkRepository):
    """Qdrant + PostgreSQL hybrid chunk repository.
    
    - Embeddings stored in Qdrant for vector search
    - Metadata stored in PostgreSQL for relational queries
    - PostgreSQL embedding column set to None to save space
    """

    def __init__(self, session: AsyncSession):
        self._session = session
        self._settings = get_settings()
        self._qdrant_store = QdrantVectorStore()
```

#### 1.3 实现 `save_batch` 方法

```python
    async def _ensure_collection(self, vector_size: int = 1536) -> None:
        """Ensure Qdrant collection exists before writing."""
        client = await get_qdrant_client()
        await ensure_collection_exists(
            client=client,
            collection_name=self._settings.qdrant_collection_name,
            vector_size=vector_size,
        )

    async def save_batch(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Save chunks to both Qdrant (embeddings) and PostgreSQL (metadata)."""
        if not chunks:
            return chunks

        # 确定向量维度
        vector_size = 1536  # default
        for chunk in chunks:
            if chunk.embedding:
                vector_size = len(chunk.embedding)
                break

        # 确保 Qdrant collection 存在
        await self._ensure_collection(vector_size)

        # 写入 Qdrant
        qdrant_count = 0
        for chunk in chunks:
            if chunk.embedding:
                try:
                    await self._qdrant_store.upsert(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        project_id=chunk.project_id,
                        content=chunk.content,
                        embedding=chunk.embedding,
                        page_number=chunk.page_number,
                    )
                    qdrant_count += 1
                except Exception as e:
                    logger.error(f"[QdrantChunkRepo] Failed to upsert chunk {chunk.id}: {e}")
                    raise

        logger.info(f"[QdrantChunkRepo] Saved {qdrant_count} embeddings to Qdrant")

        # 写入 PostgreSQL（不包含 embedding）
        models = [self._to_model(chunk, include_embedding=False) for chunk in chunks]
        self._session.add_all(models)
        await self._session.flush()

        logger.info(f"[QdrantChunkRepo] Saved {len(chunks)} metadata to PostgreSQL")

        return chunks
```

#### 1.4 实现 `find_by_document` 方法

```python
    async def find_by_document(self, document_id: UUID) -> List[DocumentChunk]:
        """Find all chunks for a document from PostgreSQL."""
        result = await self._session.execute(
            select(DocumentChunkModel)
            .where(DocumentChunkModel.document_id == document_id)
            .order_by(DocumentChunkModel.chunk_index)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
```

#### 1.5 实现 `delete_by_document` 方法

```python
    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete chunks from both Qdrant and PostgreSQL."""
        # 先删除 Qdrant
        try:
            await self._qdrant_store.delete_by_document(document_id)
            logger.info(f"[QdrantChunkRepo] Deleted from Qdrant: {document_id}")
        except Exception as e:
            logger.error(f"[QdrantChunkRepo] Failed to delete from Qdrant: {e}")
            # 继续删除 PostgreSQL

        # 删除 PostgreSQL
        result = await self._session.execute(
            delete(DocumentChunkModel).where(DocumentChunkModel.document_id == document_id)
        )
        await self._session.flush()

        logger.info(f"[QdrantChunkRepo] Deleted {result.rowcount} from PostgreSQL")
        return result.rowcount

    def _to_model(self, entity: DocumentChunk, include_embedding: bool = True) -> DocumentChunkModel:
        """Convert entity to ORM model."""
        return DocumentChunkModel(
            id=entity.id,
            document_id=entity.document_id,
            project_id=entity.project_id,
            chunk_index=entity.chunk_index,
            content=entity.content,
            page_number=entity.page_number,
            embedding=entity.embedding if include_embedding else None,
            chunk_metadata=entity.metadata,
            created_at=entity.created_at,
        )

    def _to_entity(self, model: DocumentChunkModel) -> DocumentChunk:
        """Convert ORM model to entity."""
        return DocumentChunk(
            id=model.id,
            document_id=model.document_id,
            project_id=model.project_id,
            chunk_index=model.chunk_index,
            content=model.content,
            page_number=model.page_number or 0,
            embedding=list(model.embedding) if model.embedding else None,
            metadata=model.chunk_metadata,
            created_at=model.created_at,
        )
```

---

### Task 2: 创建工厂函数

#### 2.1 & 2.2 创建文件并实现函数

创建文件 `app/backend/src/research_agent/infrastructure/database/repositories/chunk_repo_factory.py`

```python
"""Factory function for ChunkRepository."""

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.domain.repositories.chunk_repo import ChunkRepository


def get_chunk_repository(session: AsyncSession) -> ChunkRepository:
    """Get ChunkRepository based on VECTOR_STORE_PROVIDER config.
    
    Args:
        session: SQLAlchemy async session
        
    Returns:
        ChunkRepository implementation:
        - QdrantChunkRepository if VECTOR_STORE_PROVIDER=qdrant
        - SQLAlchemyChunkRepository otherwise (default: pgvector)
    """
    settings = get_settings()
    
    if settings.vector_store_provider == "qdrant":
        from research_agent.infrastructure.database.repositories.qdrant_chunk_repo import (
            QdrantChunkRepository,
        )
        return QdrantChunkRepository(session)
    else:
        from research_agent.infrastructure.database.repositories.sqlalchemy_chunk_repo import (
            SQLAlchemyChunkRepository,
        )
        return SQLAlchemyChunkRepository(session)
```

---

### Task 3: 更新 documents.py

#### 3.1 添加 import

在文件顶部的 imports 中，找到：
```python
from research_agent.infrastructure.database.repositories.sqlalchemy_chunk_repo import (
    SQLAlchemyChunkRepository,
)
```

在其下方添加：
```python
from research_agent.infrastructure.database.repositories.chunk_repo_factory import (
    get_chunk_repository,
)
```

#### 3.2 替换 upload_document 函数

找到 `upload_document` 函数中的：
```python
chunk_repo = SQLAlchemyChunkRepository(session)
```

替换为：
```python
chunk_repo = get_chunk_repository(session)
```

#### 3.3 替换 get_document_chunks 函数

找到 `get_document_chunks` 函数中的：
```python
chunk_repo = SQLAlchemyChunkRepository(session)
```

替换为：
```python
chunk_repo = get_chunk_repository(session)
```

#### 3.4 替换 delete_document 函数

找到 `delete_document` 函数中的：
```python
chunk_repo = SQLAlchemyChunkRepository(session)
```

替换为：
```python
chunk_repo = get_chunk_repository(session)
```

---

### Task 4: 搜索其他使用位置

运行命令搜索其他使用 `SQLAlchemyChunkRepository` 的地方：

```bash
grep -r "SQLAlchemyChunkRepository" app/backend/src/
```

如果找到其他位置，同样替换为 `get_chunk_repository(session)`

---

### Task 5: 验证测试

1. 确保 `.env` 中设置：
   ```
   VECTOR_STORE_PROVIDER=qdrant
   QDRANT_URL=http://localhost:6333
   QDRANT_COLLECTION_NAME=document_chunks
   ```

2. 启动 Qdrant：
   ```bash
   docker-compose up -d qdrant
   ```

3. 启动后端服务，上传一个 PDF 文档

4. 验证 Qdrant 中有数据：
   ```bash
   curl http://localhost:6333/collections/document_chunks
   ```

5. 删除文档，验证 Qdrant 中数据被删除

---

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `infrastructure/database/repositories/qdrant_chunk_repo.py` | 新增 | QdrantChunkRepository 实现 |
| `infrastructure/database/repositories/chunk_repo_factory.py` | 新增 | 工厂函数 |
| `api/v1/documents.py` | 修改 | 使用工厂函数替换硬编码 |
| 其他使用 SQLAlchemyChunkRepository 的文件 | 修改 | 使用工厂函数替换 |
