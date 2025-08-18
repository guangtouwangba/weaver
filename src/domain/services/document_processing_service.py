"""Document processing domain service."""

from typing import List, Dict, Any, Optional
from ..entities.document import Document


class DocumentProcessingService:
    """Domain service for document processing operations."""
    
    def __init__(self):
        """Initialize document processing service."""
        pass
    
    async def validate_document_for_processing(self, document: Document) -> List[str]:
        """
        Validate document for processing.
        
        Args:
            document: Document to validate
            
        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []
        
        if not document.content and not document.file_path:
            errors.append("Document must have either content or file path")
        
        if document.file_size > 100 * 1024 * 1024:  # 100MB
            errors.append("Document size exceeds maximum limit")
        
        if not document.title:
            errors.append("Document title is required")
        
        return errors
    
    async def extract_metadata(self, document: Document) -> Dict[str, Any]:
        """
        Extract metadata from document.
        
        Args:
            document: Document to process
            
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        metadata = {}
        
        if document.content:
            # Basic content analysis
            metadata['word_count'] = len(document.content.split())
            metadata['character_count'] = len(document.content)
            metadata['has_content'] = True
        else:
            metadata['has_content'] = False
        
        metadata['file_size_mb'] = document.file_size_mb
        metadata['content_type'] = document.content_type
        
        return metadata
    
    async def calculate_processing_priority(self, document: Document) -> int:
        """
        Calculate processing priority for document.
        
        Args:
            document: Document to evaluate
            
        Returns:
            int: Priority score (higher = more priority)
        """
        priority = 0
        
        # Size factor (smaller files get higher priority)
        if document.file_size < 1024 * 1024:  # < 1MB
            priority += 10
        elif document.file_size < 10 * 1024 * 1024:  # < 10MB
            priority += 5
        
        # Content type factor
        if document.content_type in ['text/plain', 'text/markdown']:
            priority += 5
        
        # Topic association factor
        if document.topic_id:
            priority += 3
        
        return priority
