"""Topic repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.topic import Topic, TopicStatus


class TopicRepository(ABC):
    """Topic repository interface defining topic persistence operations."""
    
    @abstractmethod
    async def save(self, topic: Topic) -> str:
        """
        Save a topic.
        
        Args:
            topic: Topic entity to save
            
        Returns:
            str: Topic ID
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, topic_id: str) -> Optional[Topic]:
        """
        Find topic by ID.
        
        Args:
            topic_id: Topic ID
            
        Returns:
            Optional[Topic]: Topic if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Topic]:
        """
        Find topics by user ID.
        
        Args:
            user_id: User ID
            limit: Maximum number of topics to return
            offset: Number of topics to skip
            
        Returns:
            List[Topic]: List of topics
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: TopicStatus) -> List[Topic]:
        """
        Find topics by status.
        
        Args:
            status: Topic status
            
        Returns:
            List[Topic]: List of topics
        """
        pass
    
    @abstractmethod
    async def find_by_category(self, category: str) -> List[Topic]:
        """
        Find topics by category.
        
        Args:
            category: Topic category
            
        Returns:
            List[Topic]: List of topics
        """
        pass
    
    @abstractmethod
    async def update_status(self, topic_id: str, status: TopicStatus) -> bool:
        """
        Update topic status.
        
        Args:
            topic_id: Topic ID
            status: New status
            
        Returns:
            bool: True if updated successfully
        """
        pass
    
    @abstractmethod
    async def delete(self, topic_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a topic.
        
        Args:
            topic_id: Topic ID
            hard_delete: If True, permanently delete; if False, soft delete
            
        Returns:
            bool: True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def count_by_user_id(self, user_id: str) -> int:
        """
        Count topics by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            int: Number of topics
        """
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get topic repository statistics.
        
        Returns:
            Dict[str, Any]: Statistics including counts, statuses, etc.
        """
        pass
