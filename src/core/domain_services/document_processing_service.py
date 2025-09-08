"""
Document processing domain service.

Handles document content processing operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..value_objects.document_chunk import DocumentChunk


class DocumentProcessingService(ABC):
    """Abstract domain service for document processing operations."""
    
    @abstractmethod
    def extract_text(self, file_path: str, content_type: str) -> str:
        """Extract text content from a file."""
        pass
    
    @abstractmethod
    def chunk_content(
        self, 
        content: str, 
        chunk_size: int = 1000, 
        overlap: int = 200,
        strategy: str = "fixed_size"
    ) -> List[DocumentChunk]:
        """Split content into chunks."""
        pass
    
    @abstractmethod
    def generate_summary(self, content: str, max_length: int = 200) -> str:
        """Generate a summary of the content."""
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """Extract metadata from file and content."""
        pass
    
    @abstractmethod
    def detect_language(self, content: str) -> str:
        """Detect the language of the content."""
        pass
    
    @abstractmethod
    def clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        pass
    
    @abstractmethod
    def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from content."""
        pass
    
    @abstractmethod
    def validate_content(self, content: str) -> bool:
        """Validate if content is suitable for processing."""
        pass