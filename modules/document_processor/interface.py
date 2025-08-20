"""
Document Processor Interface

Defines the contract for document processing implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from enum import Enum

from ..models import (
    Document, DocumentChunk, ProcessingResult, ModuleInterface, 
    ModuleConfig, DocumentProcessorError
)


class ChunkingStrategy(Enum):
    """Document chunking strategies."""
    FIXED_SIZE = "fixed_size"
    SENTENCE_BASED = "sentence_based"
    PARAGRAPH_BASED = "paragraph_based"
    SEMANTIC = "semantic"


class IDocumentProcessor(ModuleInterface):
    """Document processor interface."""
    
    @abstractmethod
    async def process_document(self, document: Document) -> ProcessingResult:
        """
        Process a document and create chunks.
        
        Args:
            document: Document to process
            
        Returns:
            ProcessingResult: Processing result with chunks
            
        Raises:
            DocumentProcessorError: If processing fails
        """
        pass
    
    @abstractmethod
    async def create_chunks(self, document: Document) -> List[DocumentChunk]:
        """
        Create chunks from a document.
        
        Args:
            document: Document to chunk
            
        Returns:
            List[DocumentChunk]: List of document chunks
            
        Raises:
            DocumentProcessorError: If chunking fails
        """
        pass
    
    @abstractmethod
    def get_chunking_strategy(self) -> ChunkingStrategy:
        """
        Get the chunking strategy used by this processor.
        
        Returns:
            ChunkingStrategy: The chunking strategy
        """
        pass
    
    def estimate_chunk_count(self, document: Document) -> int:
        """
        Estimate the number of chunks that will be created.
        
        Args:
            document: Document to estimate for
            
        Returns:
            int: Estimated number of chunks
        """
        if not document.content:
            return 0
        
        # Default estimation based on fixed size
        chunk_size = self.config.custom_params.get('chunk_size', 1000)
        chunk_overlap = self.config.custom_params.get('chunk_overlap', 100)
        
        content_length = len(document.content)
        effective_chunk_size = max(1, chunk_size - chunk_overlap)
        
        return max(1, (content_length + effective_chunk_size - 1) // effective_chunk_size)
    
    def validate_document(self, document: Document) -> List[str]:
        """
        Validate document for processing.
        
        Args:
            document: Document to validate
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        if not document.content:
            errors.append("Document content is empty")
        
        if not document.content.strip():
            errors.append("Document content contains only whitespace")
        
        # Check minimum content length
        min_length = self.config.custom_params.get('min_content_length', 10)
        if len(document.content.strip()) < min_length:
            errors.append(f"Document content too short (minimum: {min_length} characters)")
        
        return errors
    
    def preprocess_content(self, content: str) -> str:
        """
        Preprocess document content before chunking.
        
        Args:
            content: Raw document content
            
        Returns:
            str: Preprocessed content
        """
        if not content:
            return content
        
        # Basic preprocessing
        processed = content.strip()
        
        # Remove excessive whitespace
        import re
        processed = re.sub(r'\s+', ' ', processed)
        processed = re.sub(r'\n\s*\n', '\n\n', processed)
        
        return processed