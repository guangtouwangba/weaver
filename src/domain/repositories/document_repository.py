"""Document repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.document import Document, DocumentStatus
from ..value_objects.search_criteria import SearchCriteria


class DocumentRepository(ABC):
    """Document repository interface defining document persistence operations."""
    
    @abstractmethod
    async def save(self, document: Document) -> str:
        """
        Save a document.
        
        Args:
            document: Document entity to save
            
        Returns:
            str: Document ID
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """
        Find document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Optional[Document]: Document if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_topic_id(self, topic_id: str) -> List[Document]:
        """
        Find documents by topic ID.
        
        Args:
            topic_id: Topic ID
            
        Returns:
            List[Document]: List of documents
        """
        pass
    
    @abstractmethod
    async def find_by_owner_id(self, owner_id: str, limit: int = 50, offset: int = 0) -> List[Document]:
        """
        Find documents by owner ID.
        
        Args:
            owner_id: Owner ID
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List[Document]: List of documents
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: DocumentStatus) -> List[Document]:
        """
        Find documents by status.
        
        Args:
            status: Document status
            
        Returns:
            List[Document]: List of documents
        """
        pass
    
    @abstractmethod
    async def search(self, criteria: SearchCriteria) -> List[Document]:
        """
        Search documents based on criteria.
        
        Args:
            criteria: Search criteria
            
        Returns:
            List[Document]: List of matching documents
        """
        pass
    
    @abstractmethod
    async def update_status(self, document_id: str, status: DocumentStatus, error_message: Optional[str] = None) -> bool:
        """
        Update document status.
        
        Args:
            document_id: Document ID
            status: New status
            error_message: Error message if status is FAILED
            
        Returns:
            bool: True if updated successfully
        """
        pass
    
    @abstractmethod
    async def update_processing_results(self, document_id: str, chunk_count: int, embedding_count: int) -> bool:
        """
        Update document processing results.
        
        Args:
            document_id: Document ID
            chunk_count: Number of chunks created
            embedding_count: Number of embeddings created
            
        Returns:
            bool: True if updated successfully
        """
        pass
    
    @abstractmethod
    async def delete(self, document_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a document.
        
        Args:
            document_id: Document ID
            hard_delete: If True, permanently delete; if False, soft delete
            
        Returns:
            bool: True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def count_by_status(self, status: Optional[DocumentStatus] = None) -> int:
        """
        Count documents by status.
        
        Args:
            status: Document status (if None, count all)
            
        Returns:
            int: Number of documents
        """
        pass
    
    @abstractmethod
    async def count_by_topic_id(self, topic_id: str) -> int:
        """
        Count documents by topic ID.
        
        Args:
            topic_id: Topic ID
            
        Returns:
            int: Number of documents
        """
        pass
    
    @abstractmethod
    async def count_by_owner_id(self, owner_id: str) -> int:
        """
        Count documents by owner ID.
        
        Args:
            owner_id: Owner ID
            
        Returns:
            int: Number of documents
        """
        pass
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get document repository statistics.
        
        Returns:
            Dict[str, Any]: Statistics including counts, sizes, etc.
        """
        pass
    
    @abstractmethod
    async def save_batch(self, documents: List[Document]) -> List[str]:
        """
        Save multiple documents in batch.
        
        Args:
            documents: List of documents to save
            
        Returns:
            List[str]: List of document IDs
        """
        pass
    
    @abstractmethod
    async def find_by_ids(self, document_ids: List[str]) -> List[Document]:
        """
        Find documents by IDs.
        
        Args:
            document_ids: List of document IDs
            
        Returns:
            List[Document]: List of found documents
        """
        pass
