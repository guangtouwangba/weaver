"""
嵌入服务模块

为RAG系统提供向量嵌入生成功能，支持多种嵌入模型：
- OpenAI嵌入模型
- HuggingFace嵌入模型
- 本地嵌入模型
"""

from .base import (
    EmbeddingConfig,
    EmbeddingError,
    EmbeddingProvider,
    EmbeddingResult,
    IEmbeddingService,
)

__all__ = [
    "IEmbeddingService",
    "EmbeddingConfig",
    "EmbeddingResult",
    "EmbeddingError",
    "EmbeddingProvider",
]
