"""
Document entity.

Represents a document in the knowledge management system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4


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