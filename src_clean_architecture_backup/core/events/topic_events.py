"""
Topic domain events.

Events related to topic/knowledge management operations.
"""

from dataclasses import dataclass
from typing import Optional

from .base_event import DomainEvent


@dataclass(frozen=True)
class TopicCreatedEvent(DomainEvent):
    """Event fired when a topic is created."""
    
    name: str
    category: Optional[str] = None
    user_id: Optional[int] = None
    
    @classmethod
    def create(cls, topic_id: int, name: str, category: Optional[str] = None, 
               user_id: Optional[int] = None) -> 'TopicCreatedEvent':
        return super().create(
            aggregate_id=str(topic_id),
            name=name,
            category=category,
            user_id=user_id
        )


@dataclass(frozen=True)
class TopicUpdatedEvent(DomainEvent):
    """Event fired when a topic is updated."""
    
    name: Optional[str] = None
    description_updated: bool = False
    status_changed: bool = False
    
    @classmethod
    def create(cls, topic_id: int, name: Optional[str] = None, 
               description_updated: bool = False, status_changed: bool = False) -> 'TopicUpdatedEvent':
        return super().create(
            aggregate_id=str(topic_id),
            name=name,
            description_updated=description_updated,
            status_changed=status_changed
        )


@dataclass(frozen=True)
class TopicDeletedEvent(DomainEvent):
    """Event fired when a topic is deleted."""
    
    name: str
    
    @classmethod
    def create(cls, topic_id: int, name: str) -> 'TopicDeletedEvent':
        return super().create(
            aggregate_id=str(topic_id),
            name=name
        )


@dataclass(frozen=True)
class TopicStatisticsUpdatedEvent(DomainEvent):
    """Event fired when topic statistics are updated."""
    
    total_resources: int
    total_conversations: int
    
    @classmethod
    def create(cls, topic_id: int, total_resources: int, 
               total_conversations: int) -> 'TopicStatisticsUpdatedEvent':
        return super().create(
            aggregate_id=str(topic_id),
            total_resources=total_resources,
            total_conversations=total_conversations
        )