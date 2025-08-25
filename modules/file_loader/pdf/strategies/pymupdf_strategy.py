"""
PyMuPDF (fitz) library PDF loading strategy.

This module implements a PDF loading strategy using the PyMuPDF (fitz) library,
which provides fast and efficient PDF processing capabilities with good
performance characteristics.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, Optional

from modules.file_loader.pdf.base import IPDFLoadStrategy, PDFStrategyError
from modules.file_loader.pdf.factory import register_pdf_strategy

logger = logging.getLogger(__name__)

# Check if PyMuPDF library is available
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
    logger.info("PyMuPDF (fitz) library is available")
except ImportError:
    HAS_PYMUPDF = False
    fitz = None
    logger.warning("PyMuPDF (fitz) library is not available")


@register_pdf_strategy("pymupdf")
class PyMuPDFStrategy(IPDFLoadStrategy):
    """
    PDF loading strategy using PyMuPDF (fitz) library.
    
    This strategy leverages the PyMuPDF library to process PDF documents
    with the following capabilities:
    - Fast text extraction
    - Password-protected PDF support
    - Metadata extraction
    - Page-by-page processing
    - Configurable text extraction parameters
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PyMuPDF PDF strategy.
        
        Args:
            config: Strategy-specific configuration options
        """
        self.config = config or {}
        self._setup_default_config()
        
        logger.debug(f"PyMuPDFStrategy initialized with config: {self.config}")
    
    def _setup_default_config(self) -> None:
        """Setup default configuration values."""
        defaults = {
            "extract_images": False,
            "password": None,
            "text_sort": True,
            "flags": 0,
            "clip": None,
            "textpage_flags": 0,
            "max_file_size": 100 * 1024 * 1024  # 100MB
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    @property
    def strategy_name(self) -> str:
        """Get strategy name."""
        return "pymupdf"
    
    @property
    def priority(self) -> int:
        """Get strategy priority (lower number = higher priority)."""
        return 2  # Second priority after Unstructured
    
    async def can_handle(self, file_path: Path) -> bool:
        """
        Check if this strategy can handle the given PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            bool: True if strategy can handle the file
        """
        # Check if PyMuPDF library is available
        if not HAS_PYMUPDF:
            logger.debug("PyMuPDF library not available")
            return False
        
        # Check if file exists and has PDF extension
        if not file_path.exists() or file_path.suffix.lower() != ".pdf":
            return False
        
        try:
            # Basic file validation
            return await self.validate_file(file_path)
        except Exception as e:
            logger.warning(f"PyMuPDFStrategy cannot handle {file_path}: {e}")
            return False
    
    async def validate_file(self, file_path: Path) -> bool:
        """
        Validate PDF file for processing.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            bool: True if file is valid for processing
        """
        # Check file existence
        if not file_path.exists():
            return False
        
        # Check file extension
        if file_path.suffix.lower() != ".pdf":
            return False
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
            max_size = self.config.get("max_file_size", 100 * 1024 * 1024)
            if file_size > max_size:
                logger.warning(f"File {file_path} exceeds maximum size limit: {file_size} > {max_size}")
                return False
        except OSError as e:
            logger.error(f"Failed to get file stats for {file_path}: {e}")
            return False
        
        return True
    
    async def extract_content(self, file_path: Path, **kwargs) -> str:
        """
        Extract text content from PDF using PyMuPDF.
        
        Args:
            file_path: Path to the PDF file
            **kwargs: Additional extraction options
            
        Returns:
            str: Extracted text content
            
        Raises:
            PDFStrategyError: If content extraction fails
        """
        if not HAS_PYMUPDF:
            raise PDFStrategyError(
                "PyMuPDF library is not available",
                strategy_name=self.strategy_name,
                file_path=str(file_path)
            )
        
        try:
            # Run extraction in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                content = await loop.run_in_executor(
                    executor, 
                    self._extract_content_sync, 
                    file_path
                )
            
            if not content.strip():
                logger.warning(f"No content extracted from {file_path}")
                return ""
            
            logger.info(f"Successfully extracted {len(content)} characters from {file_path}")
            return content
            
        except Exception as e:
            error_msg = f"PyMuPDF processing failed: {str(e)}"
            logger.error(f"Failed to extract content from {file_path}: {error_msg}")
            raise PDFStrategyError(
                error_msg,
                strategy_name=self.strategy_name,
                file_path=str(file_path),
                original_error=e
            )
    
    def _extract_content_sync(self, file_path: Path) -> str:
        """
        Synchronous content extraction using PyMuPDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            str: Extracted text content
        """
        with fitz.open(str(file_path)) as doc:
            # Handle password protection
            if hasattr(doc, 'needs_pass') and doc.needs_pass:
                password = self.config.get("password")
                if password:
                    if not doc.authenticate(password):
                        raise PDFStrategyError(
                            "PDF authentication failed with provided password",
                            strategy_name=self.strategy_name,
                            file_path=str(file_path)
                        )
                else:
                    raise PDFStrategyError(
                        "PDF requires password but none provided",
                        strategy_name=self.strategy_name,
                        file_path=str(file_path)
                    )
            
            # Extract text from all pages
            content_parts = []
            text_flags = self.config.get("flags", 0)
            sort_text = self.config.get("text_sort", True)
            
            for page in doc:
                page_text = page.get_text("text", flags=text_flags, sort=sort_text)
                if page_text.strip():
                    content_parts.append(page_text.strip())
            
            return "\n\n".join(content_parts)
    
    async def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from PDF using PyMuPDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        try:
            # Run extraction in thread pool
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                metadata = await loop.run_in_executor(
                    executor,
                    self._extract_metadata_sync,
                    file_path
                )
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata from {file_path}: {e}")
            # Return fallback metadata
            return {
                "extraction_method": "pymupdf_fallback",
                "error": str(e),
                "page_count": 0,
                "title": None,
                "author": None,
                "subject": None,
                "creator": None
            }
    
    def _extract_metadata_sync(self, file_path: Path) -> Dict[str, Any]:
        """
        Synchronous metadata extraction using PyMuPDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        with fitz.open(str(file_path)) as doc:
            # Handle password protection
            if hasattr(doc, 'needs_pass') and doc.needs_pass:
                password = self.config.get("password")
                if password:
                    doc.authenticate(password)
            
            # Extract basic document metadata
            doc_metadata = doc.metadata or {}
            
            metadata = {
                "extraction_method": "pymupdf",
                "page_count": doc.page_count,
                "title": doc_metadata.get("title"),
                "author": doc_metadata.get("author"), 
                "subject": doc_metadata.get("subject"),
                "creator": doc_metadata.get("creator"),
                "producer": doc_metadata.get("producer"),
                "creation_date": doc_metadata.get("creationDate"),
                "modification_date": doc_metadata.get("modDate"),
                "keywords": doc_metadata.get("keywords"),
                "is_encrypted": doc.needs_pass,
                "permissions": doc.permissions if hasattr(doc, 'permissions') else None
            }
            
            # Add file size information
            try:
                file_stats = file_path.stat()
                metadata["file_size"] = file_stats.st_size
                metadata["file_modified"] = file_stats.st_mtime
            except OSError:
                pass
            
            return metadata