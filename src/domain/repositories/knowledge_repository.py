"""Knowledge repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.knowledge_base import Knowledge, KnowledgeBase, KnowledgeType


class KnowledgeRepository(ABC):
    """Knowledge repository interface defining knowledge persistence operations."""
    
    @abstractmethod
    async def save_knowledge(self, knowledge: Knowledge) -> str:
        """
        Save a knowledge item.
        
        Args:
            knowledge: Knowledge entity to save
            
        Returns:
            str: Knowledge ID
        """
        pass
    
    @abstractmethod
    async def save_knowledge_base(self, knowledge_base: KnowledgeBase) -> str:
        """
        Save a knowledge base.
        
        Args:
            knowledge_base: Knowledge base entity to save
            
        Returns:
            str: Knowledge base ID
        """
        pass
    
    @abstractmethod
    async def find_knowledge_by_id(self, knowledge_id: str) -> Optional[Knowledge]:
        """
        Find knowledge by ID.
        
        Args:
            knowledge_id: Knowledge ID
            
        Returns:
            Optional[Knowledge]: Knowledge if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_knowledge_base_by_id(self, kb_id: str) -> Optional[KnowledgeBase]:
        """
        Find knowledge base by ID.
        
        Args:
            kb_id: Knowledge base ID
            
        Returns:
            Optional[KnowledgeBase]: Knowledge base if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_knowledge_by_document_id(self, document_id: str) -> List[Knowledge]:
        """
        Find knowledge by source document ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            List[Knowledge]: List of knowledge items
        """
        pass
    
    @abstractmethod
    async def find_knowledge_by_type(self, knowledge_type: KnowledgeType) -> List[Knowledge]:
        """
        Find knowledge by type.
        
        Args:
            knowledge_type: Knowledge type
            
        Returns:
            List[Knowledge]: List of knowledge items
        """
        pass
    
    @abstractmethod
    async def search_knowledge(self, query: str, limit: int = 10) -> List[Knowledge]:
        """
        Search knowledge by content.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List[Knowledge]: List of matching knowledge items
        """
        pass
    
    @abstractmethod
    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        Delete a knowledge item.
        
        Args:
            knowledge_id: Knowledge ID
            
        Returns:
            bool: True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """
        Delete a knowledge base.
        
        Args:
            kb_id: Knowledge base ID
            
        Returns:
            bool: True if deleted successfully
        """
        pass
