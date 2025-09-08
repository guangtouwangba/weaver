"""
Document entity.

Represents a document in the knowledge management system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from ..events.base_event import DomainEvent


@dataclass
class Document:
    """Document entity representing a processed document in the system."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    content: Optional[str] = None
    content_type: str = "text"
    
    # File association
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    file_size: int = 0
    
    # Processing status
    status: str = "pending"
    processing_status: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Domain events
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False)
    
    def update_content(self, content: str) -> None:
        """Update document content and timestamp."""
        self.content = content
        self.updated_at = datetime.utcnow()
    
    def update_status(self, status: str, processing_status: Optional[str] = None) -> None:
        """Update document processing status."""
        self.status = status
        if processing_status:
            self.processing_status = processing_status
        self.updated_at = datetime.utcnow()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the document."""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_word_count(self) -> int:
        """Get the word count of the document content."""
        if not self.content:
            return 0
        return len(self.content.split())
    
    def is_processed(self) -> bool:
        """Check if the document has been successfully processed."""
        return self.status == "completed"
    
    def is_failed(self) -> bool:
        """Check if document processing has failed."""
        return self.status == "failed"
    
    def add_domain_event(self, event: DomainEvent) -> None:
        """Add a domain event."""
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get all domain events."""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear all domain events."""
        self._domain_events.clear()
    
    def mark_as_created(self) -> None:
        """Mark document as created and raise event."""
        from ..events.document_events import DocumentCreatedEvent
        event = DocumentCreatedEvent.create(
            document_id=self.id,
            title=self.title,
            content_type=self.content_type,
            file_id=self.file_id
        )
        self.add_domain_event(event)