"""
Core data models for the modular RAG system.

This module defines the essential data structures used across all modules,
providing a unified data model for the entire system.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass, field
from abc import ABC


class ProcessingStatus(Enum):
    """Document processing status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"  
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ContentType(Enum):
    """Content type enumeration."""
    TEXT = "text"
    PDF = "pdf"
    WORD = "word"
    MARKDOWN = "markdown"
    HTML = "html"
    UNKNOWN = "unknown"


@dataclass
class Document:
    """Core document model."""
    id: str
    title: str
    content: str
    content_type: ContentType
    file_path: Optional[str] = None
    file_size: int = 0
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def update_status(self, status: ProcessingStatus):
        """Update document status and timestamp."""
        self.status = status
        self.updated_at = datetime.now()


@dataclass  
class DocumentChunk:
    """Document chunk model."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    start_offset: int
    end_offset: int
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result of a processing operation."""
    success: bool
    document_id: Optional[str] = None
    chunks_created: int = 0
    processing_time_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchQuery:
    """Search query model."""
    query: str
    max_results: int = 10
    document_ids: Optional[List[str]] = None
    content_types: Optional[List[ContentType]] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass  
class SearchResult:
    """Search result model."""
    chunk: DocumentChunk
    score: float
    rank: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Search response model."""
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# Configuration models
@dataclass
class ModuleConfig:
    """Base configuration for modules."""
    enabled: bool = True
    max_file_size_mb: int = 100
    timeout_seconds: int = 60
    batch_size: int = 10
    custom_params: Dict[str, Any] = field(default_factory=dict)


# Exception classes
class ModuleError(Exception):
    """Base exception for module errors."""
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class FileLoaderError(ModuleError):
    """File loader specific errors."""
    pass


class DocumentProcessorError(ModuleError):
    """Document processor specific errors."""
    pass


class VectorStoreError(ModuleError):
    """Vector store specific errors."""
    pass


class KnowledgeStoreError(ModuleError):
    """Knowledge store specific errors."""
    pass


class RetrieverError(ModuleError):
    """Retriever specific errors."""
    pass


class RouterError(ModuleError):
    """Router specific errors."""
    pass


class IndexError(ModuleError):
    """Index specific errors."""
    pass


# Interface base class
class ModuleInterface(ABC):
    """Base interface for all modules."""
    
    def __init__(self, config: ModuleConfig):
        self.config = config
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize the module."""
        self.is_initialized = True
    
    async def cleanup(self):
        """Cleanup module resources."""
        self.is_initialized = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get module status."""
        return {
            "initialized": self.is_initialized,
            "enabled": self.config.enabled,
            "module_type": self.__class__.__name__
        }