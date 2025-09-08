"""
Document repository interface.

Defines the contract for document data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.document import Document
from ..value_objects.document_chunk import DocumentChunk


class DocumentRepository(ABC):
    """Abstract repository interface for document operations."""
    
    @abstractmethod
    async def save(self, document: Document) -> None:
        """Save a document."""
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        pass
    
    @abstractmethod
    async def get_by_file_id(self, file_id: str) -> List[Document]:
        """Get documents by file ID."""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Document]:
        """Search documents by content."""
        pass
    
    @abstractmethod
    async def list_by_status(self, status: str, limit: int = 100) -> List[Document]:
        """List documents by status."""
        pass
    
    @abstractmethod
    async def update_status(self, document_id: str, status: str, processing_status: Optional[str] = None) -> bool:
        """Update document status."""
        pass
    
    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete a document."""
        pass
    
    @abstractmethod
    async def count_by_status(self, status: str) -> int:
        """Count documents by status."""
        pass
    
    # Document chunk operations
    @abstractmethod
    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Save document chunks."""
        pass
    
    @abstractmethod
    async def get_chunks_by_document_id(self, document_id: str) -> List[DocumentChunk]:
        """Get chunks for a document."""
        pass
    
    @abstractmethod
    async def delete_chunks_by_document_id(self, document_id: str) -> bool:
        """Delete all chunks for a document."""
        pass
    
    @abstractmethod
    async def search_chunks(self, query: str, limit: int = 10) -> List[DocumentChunk]:
        """Search document chunks."""
        pass