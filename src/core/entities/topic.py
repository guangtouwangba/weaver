"""
Topic entity.

Represents a topic/knowledge area in the system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class TopicStatus(str, Enum):
    """Topic status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    COMPLETED = "completed"


@dataclass
class Topic:
    """Topic entity representing a knowledge area or subject."""
    
    id: int = 0
    name: str = ""
    description: Optional[str] = None
    category: Optional[str] = None
    status: TopicStatus = TopicStatus.ACTIVE
    
    # Statistics
    total_resources: int = 0
    total_conversations: int = 0
    core_concepts_discovered: int = 0
    concept_relationships: int = 0
    missing_materials_count: int = 0
    
    # Associations
    user_id: Optional[int] = None
    conversation_id: Optional[str] = None
    parent_topic_id: Optional[int] = None
    
    # Configuration
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def update_description(self, description: str) -> None:
        """Update topic description."""
        self.description = description
        self.updated_at = datetime.utcnow()
    
    def set_category(self, category: str) -> None:
        """Set topic category."""
        self.category = category
        self.updated_at = datetime.utcnow()
    
    def change_status(self, status: TopicStatus) -> None:
        """Change topic status."""
        self.status = status
        self.updated_at = datetime.utcnow()
    
    def increment_resources(self) -> None:
        """Increment total resources count."""
        self.total_resources += 1
        self.updated_at = datetime.utcnow()
    
    def increment_conversations(self) -> None:
        """Increment total conversations count."""
        self.total_conversations += 1
        self.updated_at = datetime.utcnow()
    
    def update_setting(self, key: str, value: Any) -> None:
        """Update a configuration setting."""
        self.settings[key] = value
        self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """Check if topic is active."""
        return self.status == TopicStatus.ACTIVE
    
    def is_archived(self) -> bool:
        """Check if topic is archived."""
        return self.status == TopicStatus.ARCHIVED