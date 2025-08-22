"""
RAG (Retrieval-Augmented Generation) Module

Contains RAG system-specific components:
- processors: Document processors
- orchestrator: RAG orchestrator  
- router: Document router
- api: RAG-specific API
- embedding: Embedding service
- vector_store: Vector storage
- search: Search service
"""

# RAG processors
from .processors import (
    IDocumentProcessor, DocumentProcessorError,
    TextProcessor, ChunkingProcessor
)

# RAG orchestrator
from .orchestrator import (
    IOrchestrator, OrchestrationError,
    DocumentOrchestrator
)

# RAG router
from .router import (
    IRouter, DocumentRouter
)

# RAG embedding service
from .embedding import (
    IEmbeddingService, EmbeddingProvider, EmbeddingConfig, EmbeddingResult, EmbeddingError
)

# RAG vector storage
from .vector_store import (
    IVectorStore, VectorStoreProvider, VectorStoreConfig, VectorDocument, 
    SearchResult, SearchFilter, VectorStoreError
)

# RAG processing pipeline
from .pipeline import (
    IDocumentPipeline, PipelineConfig, DocumentProcessingRequest, 
    DocumentProcessingResult, PipelineStatus, ProcessingStage, PipelineError
)

__all__ = [
    # Processors
    'IDocumentProcessor', 'DocumentProcessorError',
    'TextProcessor', 'ChunkingProcessor',
    
    # Orchestrator
    'IOrchestrator', 'OrchestrationError', 
    'DocumentOrchestrator',
    
    # Router
    'IRouter', 'DocumentRouter',
    
    # Embedding service
    'IEmbeddingService', 'EmbeddingProvider', 'EmbeddingConfig', 
    'EmbeddingResult', 'EmbeddingError',
    
    # Vector storage
    'IVectorStore', 'VectorStoreProvider', 'VectorStoreConfig', 
    'VectorDocument', 'SearchResult', 'SearchFilter', 'VectorStoreError',
    
    # Processing pipeline
    'IDocumentPipeline', 'PipelineConfig', 'DocumentProcessingRequest', 
    'DocumentProcessingResult', 'PipelineStatus', 'ProcessingStage', 'PipelineError',
]