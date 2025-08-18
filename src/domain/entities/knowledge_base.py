"""Knowledge base domain entities."""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import uuid


class KnowledgeType(Enum):
    """Type of knowledge extracted."""
    CONCEPT = "concept"
    FACT = "fact"
    PROCEDURE = "procedure"
    EXAMPLE = "example"
    DEFINITION = "definition"
    RELATIONSHIP = "relationship"


@dataclass
class Knowledge:
    """Knowledge entity representing extracted knowledge."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    knowledge_type: KnowledgeType = KnowledgeType.CONCEPT
    
    # Source information
    source_document_id: str = ""
    source_chunk_id: Optional[str] = None
    source_location: Optional[str] = None  # Page, section, etc.
    
    # Metadata
    confidence_score: float = 0.0
    relevance_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Relationships
    related_knowledge_ids: List[str] = field(default_factory=list)
    topic_ids: List[str] = field(default_factory=list)
    
    # Timestamps
    extracted_at: datetime = field(default_factory=datetime.now)
    validated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.content.strip():
            raise ValueError("Knowledge content cannot be empty")
        if not self.source_document_id:
            raise ValueError("Source document ID is required")
    
    def add_tag(self, tag: str) -> None:
        """Add tag to knowledge."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def add_related_knowledge(self, knowledge_id: str) -> None:
        """Add related knowledge."""
        if knowledge_id not in self.related_knowledge_ids:
            self.related_knowledge_ids.append(knowledge_id)
    
    def add_to_topic(self, topic_id: str) -> None:
        """Associate knowledge with topic."""
        if topic_id not in self.topic_ids:
            self.topic_ids.append(topic_id)
    
    def validate(self) -> None:
        """Mark knowledge as validated."""
        self.validated_at = datetime.now()
    
    @property
    def is_validated(self) -> bool:
        """Check if knowledge is validated."""
        return self.validated_at is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'content': self.content,
            'knowledge_type': self.knowledge_type.value,
            'source_document_id': self.source_document_id,
            'source_chunk_id': self.source_chunk_id,
            'source_location': self.source_location,
            'confidence_score': self.confidence_score,
            'relevance_score': self.relevance_score,
            'tags': self.tags,
            'metadata': self.metadata,
            'related_knowledge_ids': self.related_knowledge_ids,
            'topic_ids': self.topic_ids,
            'extracted_at': self.extracted_at.isoformat(),
            'validated_at': self.validated_at.isoformat() if self.validated_at else None,
            'is_validated': self.is_validated
        }


@dataclass 
class KnowledgeBase:
    """Knowledge base aggregate representing a collection of knowledge."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None
    
    # Knowledge collection
    knowledge_items: List[Knowledge] = field(default_factory=list)
    
    # Statistics
    total_knowledge_count: int = 0
    validated_knowledge_count: int = 0
    
    # Organization
    topics: List[str] = field(default_factory=list)  # Topic IDs
    owner_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Post-initialization setup."""
        if not self.name.strip():
            raise ValueError("Knowledge base name cannot be empty")
        self._update_statistics()
    
    def add_knowledge(self, knowledge: Knowledge) -> None:
        """Add knowledge to the knowledge base."""
        if knowledge not in self.knowledge_items:
            self.knowledge_items.append(knowledge)
            self.updated_at = datetime.now()
            self._update_statistics()
    
    def remove_knowledge(self, knowledge_id: str) -> bool:
        """Remove knowledge from the knowledge base."""
        for i, knowledge in enumerate(self.knowledge_items):
            if knowledge.id == knowledge_id:
                self.knowledge_items.pop(i)
                self.updated_at = datetime.now()
                self._update_statistics()
                return True
        return False
    
    def get_knowledge_by_type(self, knowledge_type: KnowledgeType) -> List[Knowledge]:
        """Get knowledge by type."""
        return [k for k in self.knowledge_items if k.knowledge_type == knowledge_type]
    
    def get_knowledge_by_topic(self, topic_id: str) -> List[Knowledge]:
        """Get knowledge associated with a topic."""
        return [k for k in self.knowledge_items if topic_id in k.topic_ids]
    
    def search_knowledge(self, query: str) -> List[Knowledge]:
        """Simple text search in knowledge content."""
        query_lower = query.lower()
        return [
            k for k in self.knowledge_items 
            if query_lower in k.content.lower()
        ]
    
    def _update_statistics(self) -> None:
        """Update internal statistics."""
        self.total_knowledge_count = len(self.knowledge_items)
        self.validated_knowledge_count = sum(
            1 for k in self.knowledge_items if k.is_validated
        )
    
    @property
    def validation_rate(self) -> float:
        """Get validation rate."""
        if self.total_knowledge_count == 0:
            return 0.0
        return self.validated_knowledge_count / self.total_knowledge_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'total_knowledge_count': self.total_knowledge_count,
            'validated_knowledge_count': self.validated_knowledge_count,
            'validation_rate': self.validation_rate,
            'topics': self.topics,
            'owner_id': self.owner_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
