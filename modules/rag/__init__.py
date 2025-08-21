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

# RAG处理器
from .processors import (
    IDocumentProcessor, DocumentProcessorError,
    TextProcessor, ChunkingProcessor
)

# RAG编排器
from .orchestrator import (
    IOrchestrator, OrchestrationError,
    DocumentOrchestrator
)

# RAG路由器
from .router import (
    IRouter, DocumentRouter
)

# RAG嵌入服务
from .embedding import (
    IEmbeddingService, EmbeddingProvider, EmbeddingConfig, EmbeddingResult, EmbeddingError
)

# RAG向量存储
from .vector_store import (
    IVectorStore, VectorStoreProvider, VectorStoreConfig, VectorDocument, 
    SearchResult, SearchFilter, VectorStoreError
)

# RAG处理管道
from .pipeline import (
    IDocumentPipeline, PipelineConfig, DocumentProcessingRequest, 
    DocumentProcessingResult, PipelineStatus, ProcessingStage, PipelineError
)

__all__ = [
    # 处理器
    'IDocumentProcessor', 'DocumentProcessorError',
    'TextProcessor', 'ChunkingProcessor',
    
    # 编排器
    'IOrchestrator', 'OrchestrationError', 
    'DocumentOrchestrator',
    
    # 路由器
    'IRouter', 'DocumentRouter',
    
    # 嵌入服务
    'IEmbeddingService', 'EmbeddingProvider', 'EmbeddingConfig', 
    'EmbeddingResult', 'EmbeddingError',
    
    # 向量存储
    'IVectorStore', 'VectorStoreProvider', 'VectorStoreConfig', 
    'VectorDocument', 'SearchResult', 'SearchFilter', 'VectorStoreError',
    
    # 处理管道
    'IDocumentPipeline', 'PipelineConfig', 'DocumentProcessingRequest', 
    'DocumentProcessingResult', 'PipelineStatus', 'ProcessingStage', 'PipelineError',
]