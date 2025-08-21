"""
向量存储模块

为RAG系统提供向量存储和相似性搜索功能，支持多种向量数据库：
- Weaviate
- pgvector (PostgreSQL)
- ChromaDB
- Qdrant
- Milvus
"""

from .base import (
    IVectorStore,
    VectorStoreConfig,
    VectorDocument,
    SearchResult,
    SearchFilter,
    BulkOperationResult,
    VectorStoreError,
    VectorStoreProvider,
    SimilarityMetric
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
    "SimilarityMetric"
]