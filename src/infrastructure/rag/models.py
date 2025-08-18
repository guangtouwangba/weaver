"""
Core data models for the RAG system.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


class DocumentStatus(Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class Document:
    """Core document model."""
    id: str
    title: str
    content: str
    file_type: str
    file_size: int
    file_path: Optional[str] = None
    status: DocumentStatus = DocumentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def update_status(self, status: DocumentStatus):
        """Update document status and timestamp."""
        self.status = status
        self.updated_at = datetime.now()


@dataclass
class SearchFilter:
    """Search filter for document queries."""
    document_ids: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    statuses: Optional[List[DocumentStatus]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    tags: Optional[List[str]] = None
    min_file_size: Optional[int] = None
    max_file_size: Optional[int] = None


@dataclass
class IndexInfo:
    """Index information model."""
    name: str
    type: str
    size: int
    created_at: datetime
    last_updated: datetime
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkInfo:
    """Document chunk information."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    start_position: int
    end_position: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentChunk:
    """Document chunk model for vector storage."""
    id: str
    document_id: str
    content: str
    chunk_index: int
    start_position: int
    end_position: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RetrievalResult:
    """Retrieval result model."""
    document_id: str
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryResult:
    """Query result model."""
    chunks: List[DocumentChunk]
    query: str
    total_results: int
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Document processing result."""
    success: bool
    document_id: str
    message: str = ""
    chunks_created: int = 0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)