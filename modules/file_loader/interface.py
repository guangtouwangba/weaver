"""
File Loader Interface

Defines the contract for file loading implementations.
"""

from abc import ABC, abstractmethod
from typing import List, AsyncIterator
from pathlib import Path

from ..models import (
    Document, ProcessingResult, ContentType, ModuleInterface, 
    ModuleConfig, FileLoaderError
)


class IFileLoader(ModuleInterface):
    """File loader interface."""
    
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """
        Get supported file formats.
        
        Returns:
            List[str]: List of supported file extensions (e.g., ['.txt', '.pdf'])
        """
        pass
    
    @abstractmethod
    async def load_document(self, file_path: str) -> Document:
        """
        Load a single document.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Document: Loaded document
            
        Raises:
            FileLoaderError: If file cannot be loaded
        """
        pass
    
    @abstractmethod
    async def load_documents_batch(self, file_paths: List[str]) -> AsyncIterator[ProcessingResult]:
        """
        Load multiple documents in batch.
        
        Args:
            file_paths: List of file paths
            
        Yields:
            ProcessingResult: Result for each file loading attempt
        """
        pass
    
    def can_handle(self, file_path: str) -> bool:
        """
        Check if this loader can handle the file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if can handle
        """
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_formats()
    
    def detect_content_type(self, file_path: str) -> ContentType:
        """
        Detect content type from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            ContentType: Detected content type
        """
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.txt']:
            return ContentType.TEXT
        elif ext in ['.pdf']:
            return ContentType.PDF
        elif ext in ['.doc', '.docx']:
            return ContentType.WORD
        elif ext in ['.md', '.markdown']:
            return ContentType.MARKDOWN
        elif ext in ['.html', '.htm']:
            return ContentType.HTML
        else:
            return ContentType.UNKNOWN
    
    def validate_file(self, file_path: str) -> List[str]:
        """
        Validate file before loading.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            errors.append(f"File not found: {file_path}")
            return errors
        
        # Check if it's a file (not directory)
        if not path.is_file():
            errors.append(f"Path is not a file: {file_path}")
            return errors
        
        # Check file size
        file_size = path.stat().st_size
        max_size = self.config.max_file_size_mb * 1024 * 1024
        if file_size > max_size:
            errors.append(f"File too large: {file_size / (1024*1024):.1f}MB > {max_size / (1024*1024)}MB")
        
        # Check format support
        if not self.can_handle(file_path):
            errors.append(f"Unsupported file format: {path.suffix}")
        
        return errors
    
    async def extract_metadata(self, file_path: str) -> dict:
        """
        Extract basic file metadata.
        
        Args:
            file_path: Path to the file
            
        Returns:
            dict: File metadata
        """
        path = Path(file_path)
        stat = path.stat()
        
        return {
            'file_name': path.name,
            'file_size': stat.st_size,
            'file_extension': path.suffix.lower(),
            'created_time': stat.st_ctime,
            'modified_time': stat.st_mtime,
            'absolute_path': str(path.absolute())
        }