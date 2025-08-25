"""
Unstructured library PDF loading strategy.

This module implements a PDF loading strategy using the Unstructured library,
which provides advanced capabilities for document processing including OCR,
table extraction, and structured element identification.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, List, Optional

# 抑制Unstructured的语言检测警告
unstructured_logger = logging.getLogger('unstructured')
unstructured_logger.setLevel(logging.ERROR)

from modules.file_loader.pdf.base import IPDFLoadStrategy, PDFStrategyError
from modules.file_loader.pdf.factory import register_pdf_strategy

logger = logging.getLogger(__name__)

# Check if Unstructured library is available
try:
    from unstructured.partition.pdf import partition_pdf
    HAS_UNSTRUCTURED = True
    logger.info("Unstructured library is available")
except ImportError:
    HAS_UNSTRUCTURED = False
    partition_pdf = None
    logger.warning("Unstructured library is not available")


@register_pdf_strategy("unstructured")
class UnstructuredStrategy(IPDFLoadStrategy):
    """
    PDF loading strategy using Unstructured library.
    
    This strategy leverages the Unstructured library to process PDF documents
    with advanced capabilities including:
    - High-resolution text extraction
    - OCR support for scanned documents
    - Table and structure recognition
    - Multiple language support
    - Image extraction capabilities
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Unstructured PDF strategy.
        
        Args:
            config: Strategy-specific configuration options
        """
        self.config = config or {}
        self._setup_default_config()
        
        # Language code mapping for Unstructured OCR
        self._language_map = {
            "chinese": "chi_sim",
            "zh-cn": "chi_sim", 
            "zh": "chi_sim",
            "english": "eng",
            "en": "eng",
            "japanese": "jpn",
            "jp": "jpn",
            "korean": "kor",
            "ko": "kor",
            "spanish": "spa",
            "es": "spa",
            "french": "fra",
            "fr": "fra",
            "german": "deu", 
            "de": "deu"
        }
        
        logger.debug(f"UnstructuredStrategy initialized with config: {self.config}")
    
    def _setup_default_config(self) -> None:
        """Setup default configuration values."""
        defaults = {
            "parsing_strategy": "hi_res",
            "ocr_languages": ["eng", "chi_sim"],
            "extract_images": False,
            "infer_table_structure": True,
            "timeout": 300,
            "include_page_breaks": True,
            "extract_images_in_pdf": False,
            "chunking_strategy": "by_title",
            "max_file_size": 100 * 1024 * 1024  # 100MB
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    @property
    def strategy_name(self) -> str:
        """Get strategy name."""
        return "unstructured"
    
    @property
    def priority(self) -> int:
        """Get strategy priority (lower number = higher priority)."""
        return 1  # Highest priority due to advanced capabilities
    
    async def can_handle(self, file_path: Path) -> bool:
        """
        Check if this strategy can handle the given PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            bool: True if strategy can handle the file
        """
        # Check if Unstructured library is available
        if not HAS_UNSTRUCTURED:
            logger.debug("Unstructured library not available")
            return False
        
        # Check if file exists and has PDF extension
        if not file_path.exists() or file_path.suffix.lower() != ".pdf":
            return False
        
        try:
            # Basic file validation
            return await self.validate_file(file_path)
        except Exception as e:
            logger.warning(f"UnstructuredStrategy cannot handle {file_path}: {e}")
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
        Extract text content from PDF using Unstructured.
        
        Args:
            file_path: Path to the PDF file
            **kwargs: Additional extraction options
            
        Returns:
            str: Extracted text content
            
        Raises:
            PDFStrategyError: If content extraction fails
        """
        if not HAS_UNSTRUCTURED:
            raise PDFStrategyError(
                "Unstructured library is not available",
                strategy_name=self.strategy_name,
                file_path=str(file_path)
            )
        
        try:
            # Prepare extraction parameters
            extraction_params = {
                "strategy": self.config.get("parsing_strategy", "hi_res"),
                "infer_table_structure": self.config.get("infer_table_structure", True),
                "include_page_breaks": self.config.get("include_page_breaks", True)
            }
            
            # Add OCR language settings if specified
            ocr_languages = self.config.get("ocr_languages", ["eng"])
            if ocr_languages:
                validated_languages = self._validate_language_codes(ocr_languages)
                if validated_languages:
                    extraction_params["languages"] = validated_languages
            
            # Add other configuration options
            if self.config.get("extract_images_in_pdf"):
                extraction_params["extract_images_in_pdf"] = True
            
            # Run extraction in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                elements = await loop.run_in_executor(
                    executor, 
                    lambda: partition_pdf(str(file_path), **extraction_params)
                )
            
            # Convert elements to text
            content_parts = []
            for element in elements:
                element_text = str(element).strip()
                if element_text:
                    content_parts.append(element_text)
            
            content = "\n\n".join(content_parts)
            
            if not content.strip():
                logger.warning(f"No content extracted from {file_path}")
                return ""
            
            logger.info(f"Successfully extracted {len(content)} characters from {file_path}")
            return content
            
        except Exception as e:
            error_msg = f"Unstructured processing failed: {str(e)}"
            logger.error(f"Failed to extract content from {file_path}: {error_msg}")
            raise PDFStrategyError(
                error_msg,
                strategy_name=self.strategy_name,
                file_path=str(file_path),
                original_error=e
            )
    
    async def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from PDF using Unstructured.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        try:
            # Run extraction in thread pool
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                elements = await loop.run_in_executor(
                    executor,
                    lambda: partition_pdf(str(file_path), strategy="fast")
                )
            
            # Analyze elements for metadata
            metadata = {
                "extraction_method": "unstructured",
                "total_elements": len(elements),
                "title_count": 0,
                "content_length": 0,
                "page_count": 1  # Default to 1 page
            }
            
            page_breaks = 0
            for element in elements:
                # Count different element types
                if hasattr(element, 'category'):
                    if element.category == "Title":
                        metadata["title_count"] += 1
                    elif element.category == "PageBreak":
                        page_breaks += 1
                
                # Calculate content length
                element_text = str(element).strip()
                if element_text:
                    metadata["content_length"] += len(element_text)
            
            # Calculate page count based on page breaks
            if page_breaks > 0:
                metadata["page_count"] = page_breaks + 1
            
            # Add strategy configuration info
            metadata["parsing_strategy"] = self.config.get("parsing_strategy", "hi_res")
            metadata["ocr_languages"] = self.config.get("ocr_languages", ["eng"])
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata from {file_path}: {e}")
            # Return fallback metadata
            return {
                "extraction_method": "unstructured_fallback",
                "error": str(e),
                "total_elements": 0,
                "content_length": 0,
                "page_count": 1
            }
    
    def _validate_language_codes(self, language_codes: List[str]) -> List[str]:
        """
        Validate and correct language codes for OCR.
        
        Args:
            language_codes: List of language codes to validate
            
        Returns:
            List[str]: Validated and corrected language codes
        """
        validated_codes = []
        
        for code in language_codes:
            code_lower = code.lower().strip()
            
            # Check if it's already a valid Unstructured language code
            if code_lower in ["eng", "chi_sim", "chi_tra", "jpn", "kor", "spa", "fra", "deu", "rus", "por"]:
                validated_codes.append(code_lower)
            # Check if we can map it to a valid code
            elif code_lower in self._language_map:
                mapped_code = self._language_map[code_lower]
                if mapped_code not in validated_codes:
                    validated_codes.append(mapped_code)
            else:
                logger.warning(f"Invalid or unsupported language code: {code}")
        
        # Ensure we always have at least English as fallback
        if not validated_codes:
            validated_codes = ["eng"]
        
        return validated_codes