"""
Knowledge Domain Module

知识管理领域模块，包含：
- 领域实体 (Entities)
- 值对象 (Value Objects)
- 领域服务接口 (Domain Service Interfaces)
- 仓储接口 (Repository Interfaces)
- 领域事件 (Domain Events)
"""

from .interfaces import (
    # Value Objects
    DocumentId,
    ChunkId,
    
    # Enums
    ProcessingStatus,
    SearchStrategy,
    ChunkingStrategy,
    
    # Entities
    KnowledgeDocument,
    DocumentChunk,
    SearchQuery,
    SearchResult,
    
    # Repository Interfaces
    IKnowledgeRepository,
    
    # Service Interfaces
    IDocumentProcessor,
    IVectorService,
    ISearchService,
    IKnowledgeManagementService,
    
    # Domain Events
    DocumentIngested,
    DocumentProcessed,
    DocumentProcessingFailed,
)

__all__ = [
    # Value Objects
    "DocumentId",
    "ChunkId",
    
    # Enums
    "ProcessingStatus",
    "SearchStrategy", 
    "ChunkingStrategy",
    
    # Entities
    "KnowledgeDocument",
    "DocumentChunk",
    "SearchQuery",
    "SearchResult",
    
    # Repository Interfaces
    "IKnowledgeRepository",
    
    # Service Interfaces
    "IDocumentProcessor",
    "IVectorService",
    "ISearchService",
    "IKnowledgeManagementService",
    
    # Domain Events
    "DocumentIngested",
    "DocumentProcessed",
    "DocumentProcessingFailed",
]