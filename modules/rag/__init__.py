"""
RAG (Retrieval-Augmented Generation) 模块

包含RAG系统特有的组件：
- processors: 文档处理器
- orchestrator: RAG编排器
- router: 文档路由器
- api: RAG专用API
- embedding: 嵌入服务
- vector_store: 向量存储
- search: 搜索服务
"""

# RAG嵌入服务
from modules.rag.embedding import (
    EmbeddingConfig,
    EmbeddingError,
    EmbeddingProvider,
    EmbeddingResult,
    IEmbeddingService,
)

# RAG编排器
from modules.rag.orchestrator import (
    DocumentOrchestrator,
    IOrchestrator,
    OrchestrationError,
)

# RAG处理管道
from modules.rag.pipeline import (
    DocumentProcessingRequest,
    DocumentProcessingResult,
    IDocumentPipeline,
    PipelineConfig,
    PipelineError,
    PipelineStatus,
    ProcessingStage,
)

# RAG处理器
from modules.rag.processors import (
    ChunkingProcessor,
    DocumentProcessorError,
    IDocumentProcessor,
    TextProcessor,
)

# RAG路由器
from modules.rag.router import DocumentRouter, IRouter

# RAG向量存储
from modules.rag.vector_store import (
    IVectorStore,
    SearchFilter,
    SearchResult,
    VectorDocument,
    VectorStoreConfig,
    VectorStoreError,
    VectorStoreProvider,
)

__all__ = [
    # 处理器
    "IDocumentProcessor",
    "DocumentProcessorError",
    "TextProcessor",
    "ChunkingProcessor",
    # 编排器
    "IOrchestrator",
    "OrchestrationError",
    "DocumentOrchestrator",
    # 路由器
    "IRouter",
    "DocumentRouter",
    # 嵌入服务
    "IEmbeddingService",
    "EmbeddingProvider",
    "EmbeddingConfig",
    "EmbeddingResult",
    "EmbeddingError",
    # 向量存储
    "IVectorStore",
    "VectorStoreProvider",
    "VectorStoreConfig",
    "VectorDocument",
    "SearchResult",
    "SearchFilter",
    "VectorStoreError",
    # 处理管道
    "IDocumentPipeline",
    "PipelineConfig",
    "DocumentProcessingRequest",
    "DocumentProcessingResult",
    "PipelineStatus",
    "ProcessingStage",
    "PipelineError",
]
