"""Document domain entity."""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import uuid


class DocumentStatus(Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class Document:
    """Document domain entity representing a knowledge document."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    file_path: Optional[str] = None
    file_size: int = 0
    content_type: str = "text/plain"
    status: DocumentStatus = DocumentStatus.PENDING
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # Relationships
    topic_id: Optional[str] = None
    owner_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    
    # Processing results
    chunk_count: int = 0
    embedding_count: int = 0
    processing_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.title and self.file_path:
            from pathlib import Path
            self.title = Path(self.file_path).stem
            
        self.updated_at = datetime.now()
    
    def update_status(self, status: DocumentStatus, error_message: Optional[str] = None) -> None:
        """Update document processing status."""
        self.status = status
        self.updated_at = datetime.now()
        
        if status == DocumentStatus.COMPLETED:
            self.processed_at = datetime.now()
        elif status == DocumentStatus.FAILED and error_message:
            self.processing_errors.append(error_message)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to document."""
        self.metadata[key] = value
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """Add tag to document."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def update_processing_results(self, chunk_count: int, embedding_count: int) -> None:
        """Update processing results."""
        self.chunk_count = chunk_count
        self.embedding_count = embedding_count
        self.updated_at = datetime.now()
    
    @property
    def is_processed(self) -> bool:
        """Check if document is successfully processed."""
        return self.status == DocumentStatus.COMPLETED
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return self.file_size / (1024 * 1024) if self.file_size > 0 else 0.0
    
    @property
    def age_days(self) -> int:
        """Get document age in days."""
        return (datetime.now() - self.created_at).days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'content_type': self.content_type,
            'status': self.status.value,
            'metadata': self.metadata,
            'tags': self.tags,
            'topic_id': self.topic_id,
            'owner_id': self.owner_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'chunk_count': self.chunk_count,
            'embedding_count': self.embedding_count,
            'processing_errors': self.processing_errors,
            'file_size_mb': self.file_size_mb,
            'age_days': self.age_days
        }
