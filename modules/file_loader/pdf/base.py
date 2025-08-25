"""
Abstract base classes and interfaces for PDF loading strategies.

This module defines the contract that all PDF loading strategies must implement,
ensuring consistent behavior across different PDF processing libraries.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class IPDFLoadStrategy(ABC):
    """
    Abstract base class for PDF loading strategies.
    
    Each strategy implements a specific method for extracting content
    and metadata from PDF files (e.g., Unstructured, PyMuPDF, PyPDF2).
    
    This interface ensures all strategies provide consistent methods for:
    - File compatibility checking
    - Content extraction
    - Metadata extraction
    - File validation
    - Strategy identification
    """
    
    @abstractmethod
    async def can_handle(self, file_path: Path) -> bool:
        """
        Check if this strategy can handle the given PDF file.
        
        This method determines if the strategy has the necessary dependencies
        and capabilities to process the specified PDF file.
        
        Args:
            file_path: Path to the PDF file to be processed
            
        Returns:
            bool: True if strategy can process this file, False otherwise
        """
        pass
        
    @abstractmethod
    async def extract_content(self, file_path: Path, **kwargs) -> str:
        """
        Extract text content from PDF file using this strategy.
        
        This method performs the core content extraction using the strategy's
        specific PDF processing library and techniques.
        
        Args:
            file_path: Path to the PDF file
            **kwargs: Additional extraction parameters specific to the strategy
            
        Returns:
            str: Extracted text content from the PDF
            
        Raises:
            FileLoaderError: If content extraction fails
        """
        pass
        
    @abstractmethod
    async def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from PDF file using this strategy.
        
        This method extracts document metadata such as page count, author,
        title, creation date, and other PDF properties.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict[str, Any]: PDF metadata including:
                - pages: Number of pages
                - title: Document title
                - author: Document author  
                - creation_date: Creation timestamp
                - extraction_method: Strategy used for extraction
        """
        pass
        
    @abstractmethod
    async def validate_file(self, file_path: Path) -> bool:
        """
        Validate if the PDF file can be processed by this strategy.
        
        This method performs comprehensive validation including file existence,
        format verification, size checks, and strategy-specific compatibility tests.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            bool: True if file is valid and processable, False otherwise
        """
        pass
        
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """
        Get the unique identifier name of this strategy.
        
        This property provides a human-readable name for the strategy,
        used for logging, configuration, and debugging purposes.
        
        Returns:
            str: Strategy identifier (e.g., "unstructured", "pymupdf", "pypdf2")
        """
        pass
        
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Get the priority level of this strategy for automatic selection.
        
        Lower numbers indicate higher priority. This is used by the auto-selection
        mechanism to choose the best available strategy for a given PDF file.
        
        Returns:
            int: Priority level (1 = highest priority, higher numbers = lower priority)
        """
        pass


class PDFStrategyError(Exception):
    """
    Base exception for PDF strategy-related errors.
    
    This exception is raised when a PDF strategy encounters an error
    that prevents it from processing a file successfully.
    """
    
    def __init__(
        self, 
        message: str, 
        strategy_name: str = None,
        file_path: str = None,
        original_error: Exception = None
    ):
        """
        Initialize PDF strategy error.
        
        Args:
            message: Human-readable error description
            strategy_name: Name of the strategy that failed
            file_path: Path to the file being processed
            original_error: Original exception that caused this error
        """
        self.strategy_name = strategy_name
        self.file_path = file_path
        self.original_error = original_error
        super().__init__(message)
        
    def __str__(self) -> str:
        """Return formatted error message."""
        parts = [super().__str__()]
        
        if self.strategy_name:
            parts.append(f"Strategy: {self.strategy_name}")
            
        if self.file_path:
            parts.append(f"File: {self.file_path}")
            
        if self.original_error:
            parts.append(f"Cause: {str(self.original_error)}")
            
        return " | ".join(parts)


class BasePDFStrategy(IPDFLoadStrategy):
    """
    Base implementation providing common functionality for PDF strategies.
    
    This abstract class provides default implementations for common operations
    while still requiring subclasses to implement the core strategy methods.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize base PDF strategy.
        
        Args:
            config: Strategy-specific configuration parameters
        """
        self.config = config or {}
        
    async def _check_file_exists(self, file_path: Path) -> bool:
        """
        Check if file exists and is readable.
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if file exists and is readable
        """
        try:
            return file_path.exists() and file_path.is_file()
        except (OSError, PermissionError):
            return False
            
    async def _check_file_size(self, file_path: Path, max_size: int = None) -> bool:
        """
        Check if file size is within acceptable limits.
        
        Args:
            file_path: Path to check
            max_size: Maximum file size in bytes (from config if not provided)
            
        Returns:
            bool: True if file size is acceptable
        """
        try:
            if max_size is None:
                max_size = self.config.get("max_file_size", 100 * 1024 * 1024)  # 100MB default
                
            file_size = file_path.stat().st_size
            return file_size <= max_size
        except (OSError, PermissionError):
            return False
            
    async def _check_pdf_extension(self, file_path: Path) -> bool:
        """
        Check if file has PDF extension.
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if file has .pdf extension
        """
        return file_path.suffix.lower() == '.pdf'
        
    def _create_error(
        self, 
        message: str, 
        file_path: Path = None, 
        original_error: Exception = None
    ) -> PDFStrategyError:
        """
        Create a strategy-specific error with context.
        
        Args:
            message: Error description
            file_path: File being processed
            original_error: Original exception
            
        Returns:
            PDFStrategyError: Formatted error with context
        """
        return PDFStrategyError(
            message=message,
            strategy_name=self.strategy_name,
            file_path=str(file_path) if file_path else None,
            original_error=original_error
        )