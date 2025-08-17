"""
Domain entities for topic management.

This module contains the core domain entities and value objects
for the topic management system.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class TopicStatus(str, Enum):
    """Topic status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    COMPLETED = "completed"


class ResourceType(str, Enum):
    """Resource type enumeration."""
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    URL = "url"
    ARCHIVE = "archive"


class ParseStatus(str, Enum):
    """Parse status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TopicResource:
    """Domain entity for topic resources."""
    id: Optional[int] = None
    topic_id: Optional[int] = None
    original_name: str = ""
    file_name: str = ""
    file_path: str = ""
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    file_hash: Optional[str] = None
    resource_type: ResourceType = ResourceType.TEXT
    source_url: Optional[str] = None
    is_parsed: bool = False
    parse_status: ParseStatus = ParseStatus.PENDING
    parse_error: Optional[str] = None
    parse_attempts: int = 0
    total_pages: Optional[int] = None
    parsed_pages: int = 0
    content_preview: Optional[str] = None
    content_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_public: bool = False
    access_level: str = "private"
    uploaded_at: Optional[datetime] = None
    parsed_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None


@dataclass
class Tag:
    """Domain entity for tags."""
    id: Optional[int] = None
    name: str = ""
    category: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    usage_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None


@dataclass
class Conversation:
    """Domain entity for conversations."""
    id: Optional[str] = None
    topic_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    message_count: int = 0
    conversation_data: Optional[Dict[str, Any]] = None
    external_conversation_url: Optional[str] = None
    storage_type: str = "internal"
    total_tokens: int = 0
    total_cost: int = 0
    conversation_tags: List[str] = field(default_factory=list)
    last_message_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None


@dataclass
class Topic:
    """Domain entity for topics."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    category: Optional[str] = None
    status: TopicStatus = TopicStatus.ACTIVE
    
    # Learning analytics
    core_concepts_discovered: int = 0
    concept_relationships: int = 0
    missing_materials_count: int = 0
    
    # Statistics
    total_resources: int = 0
    total_conversations: int = 0
    
    # Associations
    user_id: Optional[int] = None
    conversation_id: Optional[str] = None
    parent_topic_id: Optional[int] = None
    
    # Configuration
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    
    # Related entities (loaded separately)
    parent_topic: Optional['Topic'] = None
    child_topics: List['Topic'] = field(default_factory=list)
    resources: List[TopicResource] = field(default_factory=list)
    conversations: List[Conversation] = field(default_factory=list)
    tags: List[Tag] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.last_accessed_at is None:
            self.last_accessed_at = datetime.utcnow()
    
    def add_resource(self, resource: TopicResource) -> None:
        """Add a resource to this topic."""
        resource.topic_id = self.id
        self.resources.append(resource)
        self.total_resources = len(self.resources)
        self.updated_at = datetime.utcnow()
    
    def add_conversation(self, conversation: Conversation) -> None:
        """Add a conversation to this topic."""
        conversation.topic_id = self.id
        self.conversations.append(conversation)
        self.total_conversations = len(self.conversations)
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: Tag) -> None:
        """Add a tag to this topic."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: Tag) -> None:
        """Remove a tag from this topic."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def update_learning_analytics(self, **kwargs) -> None:
        """Update learning analytics fields."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    def mark_accessed(self) -> None:
        """Mark topic as accessed."""
        self.last_accessed_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archive this topic."""
        self.status = TopicStatus.ARCHIVED
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate this topic."""
        self.status = TopicStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def complete(self) -> None:
        """Mark topic as completed."""
        self.status = TopicStatus.COMPLETED
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """Soft delete this topic."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted topic."""
        self.is_deleted = False
        self.deleted_at = None
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "status": self.status.value if isinstance(self.status, TopicStatus) else self.status,
            "core_concepts_discovered": self.core_concepts_discovered,
            "concept_relationships": self.concept_relationships,
            "missing_materials_count": self.missing_materials_count,
            "total_resources": self.total_resources,
            "total_conversations": self.total_conversations,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "parent_topic_id": self.parent_topic_id,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
    
    def __repr__(self):
        return f"Topic(id={self.id}, name={self.name}, status={self.status})"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if not isinstance(other, Topic):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id) if self.id else hash(id(self))