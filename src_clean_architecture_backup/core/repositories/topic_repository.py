"""
Topic repository interface.

Defines the contract for topic data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.topic import Topic, TopicStatus


class TopicRepository(ABC):
    """Abstract repository interface for topic operations."""
    
    @abstractmethod
    async def save(self, topic: Topic) -> None:
        """Save a topic."""
        pass
    
    @abstractmethod
    async def get_by_id(self, topic_id: int) -> Optional[Topic]:
        """Get topic by ID."""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Topic]:
        """Get topic by name."""
        pass
    
    @abstractmethod
    async def list_by_status(self, status: TopicStatus, limit: int = 100) -> List[Topic]:
        """List topics by status."""
        pass
    
    @abstractmethod
    async def list_by_user_id(self, user_id: int, limit: int = 100) -> List[Topic]:
        """List topics by user ID."""
        pass
    
    @abstractmethod
    async def list_by_parent_topic_id(self, parent_topic_id: int) -> List[Topic]:
        """List child topics by parent topic ID."""
        pass
    
    @abstractmethod
    async def search_by_name(self, name_pattern: str, limit: int = 10) -> List[Topic]:
        """Search topics by name pattern."""
        pass
    
    @abstractmethod
    async def search_by_category(self, category: str, limit: int = 10) -> List[Topic]:
        """Search topics by category."""
        pass
    
    @abstractmethod
    async def update_status(self, topic_id: int, status: TopicStatus) -> bool:
        """Update topic status."""
        pass
    
    @abstractmethod
    async def update_statistics(
        self, 
        topic_id: int, 
        total_resources: Optional[int] = None,
        total_conversations: Optional[int] = None,
        core_concepts_discovered: Optional[int] = None,
        concept_relationships: Optional[int] = None,
        missing_materials_count: Optional[int] = None
    ) -> bool:
        """Update topic statistics."""
        pass
    
    @abstractmethod
    async def delete(self, topic_id: int) -> bool:
        """Delete a topic."""
        pass
    
    @abstractmethod
    async def count_by_status(self, status: TopicStatus) -> int:
        """Count topics by status."""
        pass
    
    @abstractmethod
    async def get_active_topics(self, limit: int = 100) -> List[Topic]:
        """Get all active topics."""
        pass