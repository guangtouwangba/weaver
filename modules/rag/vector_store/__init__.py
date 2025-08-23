"""
向量存储模块

为RAG系统提供向量存储和相似性搜索功能，支持多种向量数据库：
- Weaviate
- pgvector (PostgreSQL)
- ChromaDB
- Qdrant
- Milvus
"""

from modules.rag.vector_store.base import (
    BulkOperationResult,
    IVectorStore,
    SearchFilter,
    SearchResult,
    SimilarityMetric,
    VectorDocument,
    VectorStoreConfig,
    VectorStoreError,
    VectorStoreProvider,
)

__all__ = [
    "IVectorStore",
    "VectorStoreConfig",
    "VectorDocument",
    "SearchResult",
    "SearchFilter",
    "BulkOperationResult",
    "VectorStoreError",
    "VectorStoreProvider",
    "SimilarityMetric",
]
