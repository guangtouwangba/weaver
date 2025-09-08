"""
Document domain events.

Events related to document lifecycle and operations.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from .base_event import DomainEvent


class DocumentCreatedEvent(DomainEvent):
    """Event fired when a document is created."""
    
    def __init__(self, event_id: str, occurred_at, aggregate_id: str, 
                 title: str, content_type: str, file_id: Optional[str] = None,
                 event_version: int = 1, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(event_id, occurred_at, aggregate_id, event_version, metadata)
        self.title = title
        self.content_type = content_type
        self.file_id = file_id
    
    @classmethod
    def create(cls, document_id: str, title: str, content_type: str, file_id: Optional[str] = None) -> 'DocumentCreatedEvent':
        from datetime import datetime
        from uuid import uuid4
        return cls(
            event_id=str(uuid4()),
            occurred_at=datetime.utcnow(),
            aggregate_id=document_id,
            title=title,
            content_type=content_type,
            file_id=file_id
        )


@dataclass(frozen=True)
class DocumentProcessedEvent(DomainEvent):
    """Event fired when a document has been processed (chunked and indexed)."""
    
    chunks_created: int
    processing_time: float
    
    @classmethod
    def create(cls, document_id: str, chunks_created: int, processing_time: float) -> 'DocumentProcessedEvent':
        return super().create(
            aggregate_id=document_id,
            chunks_created=chunks_created,
            processing_time=processing_time
        )


@dataclass(frozen=True)
class DocumentUpdatedEvent(DomainEvent):
    """Event fired when a document is updated."""
    
    title: Optional[str] = None
    content_updated: bool = False
    status_updated: bool = False
    
    @classmethod
    def create(cls, document_id: str, title: Optional[str] = None, 
               content_updated: bool = False, status_updated: bool = False) -> 'DocumentUpdatedEvent':
        return super().create(
            aggregate_id=document_id,
            title=title,
            content_updated=content_updated,
            status_updated=status_updated
        )


@dataclass(frozen=True)
class DocumentDeletedEvent(DomainEvent):
    """Event fired when a document is deleted."""
    
    title: str
    
    @classmethod
    def create(cls, document_id: str, title: str) -> 'DocumentDeletedEvent':
        return super().create(
            aggregate_id=document_id,
            title=title
        )


@dataclass(frozen=True)
class DocumentSearchedEvent(DomainEvent):
    """Event fired when documents are searched."""
    
    query: str
    results_count: int
    search_type: str
    
    @classmethod
    def create(cls, query: str, results_count: int, search_type: str = "semantic") -> 'DocumentSearchedEvent':
        return super().create(
            aggregate_id=f"search_{query[:50]}",  # Use query as pseudo-aggregate
            query=query,
            results_count=results_count,
            search_type=search_type
        )