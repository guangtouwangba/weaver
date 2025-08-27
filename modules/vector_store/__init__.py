"""
向量存储模块

为RAG系统提供向量存储和相似性搜索功能，支持多种向量数据库：
- Weaviate
- pgvector (PostgreSQL)
- ChromaDB
- Qdrant
- Milvus
"""

from modules.vector_store.base import (
    BulkOperationResult,
    IndexType,
    IVectorStore,
    SearchFilter,
    SearchResult,
    SimilarityMetric,
    SummaryDocument,
    VectorDocument,
    VectorStoreConfig,
    VectorStoreError,
    VectorStoreProvider,
)

__all__ = [
    "IVectorStore",
    "VectorStoreConfig",
    "VectorDocument",
    "SummaryDocument",
    "SearchResult",
    "SearchFilter",
    "BulkOperationResult",
    "VectorStoreError",
    "VectorStoreProvider",
    "SimilarityMetric",
    "IndexType",
]
