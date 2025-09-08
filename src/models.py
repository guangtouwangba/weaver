"""
All data models in one file.

Contains entities, value objects, and data transfer objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4
from enum import Enum


# Enums
class TopicStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


class FileStatus(str, Enum):
    UPLOADING = "uploading"
    AVAILABLE = "available"
    PROCESSING = "processing"
    FAILED = "failed"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Core Entities
@dataclass
class Document:
    """Document entity."""
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    content: Optional[str] = None
    content_type: str = "text"
    file_id: Optional[str] = None
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def update_content(self, content: str) -> None:
        self.content = content
        self.updated_at = datetime.utcnow()
    
    def update_status(self, status: str) -> None:
        self.status = status
        self.updated_at = datetime.utcnow()


@dataclass
class Topic:
    """Topic entity."""
    id: int = 0
    name: str = ""
    description: Optional[str] = None
    status: TopicStatus = TopicStatus.ACTIVE
    total_resources: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def update_description(self, description: str) -> None:
        self.description = description
        self.updated_at = datetime.utcnow()


@dataclass
class File:
    """File entity."""
    id: str = field(default_factory=lambda: str(uuid4()))
    filename: str = ""
    original_name: str = ""
    file_size: int = 0
    content_type: str = ""
    status: FileStatus = FileStatus.UPLOADING
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def mark_as_available(self) -> None:
        self.status = FileStatus.AVAILABLE


@dataclass
class ChatMessage:
    """Chat message value object."""
    content: str = ""
    role: MessageRole = MessageRole.USER
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatSession:
    """Chat session entity."""
    id: str = field(default_factory=lambda: str(uuid4()))
    topic_id: Optional[int] = None
    messages: List[ChatMessage] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_message(self, message: ChatMessage) -> None:
        self.messages.append(message)
    
    def get_message_count(self) -> int:
        return len(self.messages)


@dataclass
class DocumentChunk:
    """Document chunk value object."""
    id: str = field(default_factory=lambda: str(uuid4()))
    document_id: str = ""
    content: str = ""
    chunk_index: int = 0
    embedding: Optional[List[float]] = None
    
    def has_embedding(self) -> bool:
        return self.embedding is not None


# Request/Response DTOs
@dataclass
class CreateDocumentRequest:
    title: str
    content: str
    content_type: str = "text"
    file_id: Optional[str] = None


@dataclass
class SearchRequest:
    query: str
    limit: int = 10
    use_semantic: bool = True


@dataclass
class ChatRequest:
    session_id: str
    message: str
    use_context: bool = True


# Events (simplified)
@dataclass
class Event:
    """Simple event class."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def document_created(cls, document_id: str, title: str) -> 'Event':
        return cls(
            type="document_created",
            data={"document_id": document_id, "title": title}
        )
    
    @classmethod
    def document_processed(cls, document_id: str, chunks_count: int) -> 'Event':
        return cls(
            type="document_processed", 
            data={"document_id": document_id, "chunks_count": chunks_count}
        )
    
    @classmethod
    def message_sent(cls, session_id: str, message_length: int) -> 'Event':
        return cls(
            type="message_sent",
            data={"session_id": session_id, "message_length": message_length}
        )