"""
Refactored PDF File Loader using Strategy Pattern.

This module provides a clean, maintainable PDF file loader implementation
that leverages the strategy pattern for PDF processing. It replaces the
monolithic approach with a flexible, extensible architecture.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config.file_loader_config import PDFLoaderConfig
from modules.file_loader.base import FileLoaderError, IFileLoader
from modules.file_loader.factory import register_file_loader
from modules.file_loader.pdf.base import IPDFLoadStrategy, PDFStrategyError
from modules.file_loader.pdf.factory import get_pdf_strategy_factory
from modules.schemas.enums import ContentType
from modules.schemas import create_document_from_path
from modules.schemas.document import Document
from modules.models import FileLoadRequest

logger = logging.getLogger(__name__)


@register_file_loader(content_type=ContentType.PDF)
class PDFFileLoader(IFileLoader):
    """
    Refactored PDF file loader using strategy pattern.
    
    This loader delegates PDF processing to specialized strategies while
    maintaining a clean, simple interface. It supports automatic strategy
    selection, fallback handling, and comprehensive error management.
    """

    def __init__(self, config: Optional[Union[Dict[str, Any], PDFLoaderConfig]] = None):
        """
        Initialize PDF file loader with strategy pattern.

        Args:
            config: PDF loader configuration (dict or PDFLoaderConfig instance)
        """
        # Convert dict config to PDFLoaderConfig if needed
        if isinstance(config, dict):
            self.config = PDFLoaderConfig(**config)
        elif isinstance(config, PDFLoaderConfig):
            self.config = config
        else:
            self.config = PDFLoaderConfig()

        self._supported_formats = [".pdf"]
        
        logger.info(
            f"PDFFileLoader initialized with strategy: {self.config.default_strategy}, "
            f"fallback enabled: {self.config.enable_fallback}"
        )

    @property
    def loader_name(self) -> str:
        """Get loader name."""
        return "PDFFileLoader"

    def supported_formats(self) -> List[str]:
        """Get supported PDF formats."""
        return self._supported_formats.copy()

    def supports_content_type(self, content_type: ContentType) -> bool:
        """Check if specified content type is supported."""
        return content_type == ContentType.PDF

    async def validate_file(self, file_path: str) -> bool:
        """
        Validate if PDF file can be processed.

        Args:
            file_path: Path to the PDF file

        Returns:
            bool: True if file is valid and can be processed
        """
        try:
            path = Path(file_path)

            # Check file existence
            if not path.exists():
                logger.error(f"PDF file does not exist: {file_path}")
                return False

            # Check file extension
            if path.suffix.lower() not in self._supported_formats:
                logger.error(f"Unsupported file format: {path.suffix}")
                return False

            # Check file size
            file_size = path.stat().st_size
            if file_size > self.config.max_file_size:
                logger.error(
                    f"PDF file too large: {file_size} bytes > {self.config.max_file_size} bytes"
                )
                return False

            # Check if any strategy can handle the file
            try:
                factory = get_pdf_strategy_factory()
                await factory.select_best_strategy(path, self.config)
                logger.debug(f"PDF file validation successful: {file_path}")
                return True
            except PDFStrategyError as e:
                logger.error(f"No suitable PDF strategy available: {e}")
                return False

        except Exception as e:
            logger.error(f"PDF file validation failed: {e}")
            return False

    async def load_document(self, request: Union[str, FileLoadRequest, Any]) -> Document:
        """
        Load PDF document using the best available strategy.

        Args:
            request: File path string, FileLoadRequest object, or other request type

        Returns:
            Document: Loaded document with content and metadata

        Raises:
            FileLoaderError: If document loading fails
        """
        # Handle different types of input parameters
        if isinstance(request, str):
            file_path = request
            metadata = {}
        elif isinstance(request, FileLoadRequest):
            file_path = request.file_path
            metadata = request.metadata or {}
        else:
            # Handle other request types (backward compatibility)
            file_path = str(request)
            metadata = {}

        # Validate file
        if not await self.validate_file(file_path):
            raise FileLoaderError(f"PDF file validation failed: {file_path}")

        try:
            path = Path(file_path)
            
            # Get the best strategy for this file
            factory = get_pdf_strategy_factory()
            strategy = await factory.select_best_strategy(path, self.config)
            
            logger.info(f"Using PDF strategy '{strategy.strategy_name}' for file: {path.name}")

            # Extract content using selected strategy
            content = await strategy.extract_content(path)
            
            if not content or not content.strip():
                logger.warning(f"No content extracted from PDF file: {file_path}")
                content = f"[PDF file {path.name} contains no extractable text content]"

            # Extract metadata using selected strategy (with error handling)
            try:
                pdf_metadata = await strategy.extract_metadata(path)
            except Exception as e:
                logger.warning(f"Metadata extraction failed for {file_path}: {e}")
                pdf_metadata = self._get_fallback_metadata(path, strategy.strategy_name, str(e))

            # Create document object
            document = create_document_from_path(file_path, content)

            # Update document metadata
            document.metadata.update({
                "loader": self.loader_name,
                "file_size": path.stat().st_size,
                "strategy_used": strategy.strategy_name,
                "strategy_priority": strategy.priority,
                **pdf_metadata,
                **(metadata or {})  # Include any custom metadata from request
            })

            # Log successful loading
            page_count = pdf_metadata.get("page_count", "unknown")
            logger.info(
                f"Successfully loaded PDF document: {file_path} "
                f"(strategy: {strategy.strategy_name}, pages: {page_count}, "
                f"characters: {len(content)})"
            )
            
            return document

        except PDFStrategyError as e:
            logger.error(f"PDF strategy failed for {file_path}: {e}")
            raise FileLoaderError(f"PDF processing failed: {str(e)}")
        except FileLoaderError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading PDF document {file_path}: {e}")
            raise FileLoaderError(f"Failed to load PDF document: {str(e)}")

    async def load_documents_batch(self, requests: List[Union[str, FileLoadRequest, Any]]) -> List[Document]:
        """
        Batch load PDF documents.

        Args:
            requests: List of file paths, FileLoadRequest objects, or other request types

        Returns:
            List[Document]: List of successfully loaded documents
        """
        if not requests:
            logger.info("Empty batch request, returning empty list")
            return []

        documents = []
        successful_count = 0

        for i, request in enumerate(requests):
            try:
                document = await self.load_document(request)
                documents.append(document)
                successful_count += 1
                
                # Log progress for large batches
                if len(requests) > 10 and (i + 1) % 10 == 0:
                    logger.info(f"Batch progress: {i + 1}/{len(requests)} processed")

            except FileLoaderError as e:
                logger.error(f"Batch load PDF failed for request {i + 1}: {e}")
                # Continue processing other documents, do not interrupt entire batch
                continue
            except Exception as e:
                logger.error(f"Unexpected error in batch processing for request {i + 1}: {e}")
                continue

        logger.info(
            f"PDF batch loading completed: {successful_count}/{len(requests)} successful"
        )
        return documents

    def _get_fallback_metadata(self, path: Path, strategy_name: str, error: str) -> Dict[str, Any]:
        """
        Generate fallback metadata when extraction fails.

        Args:
            path: Path to the PDF file
            strategy_name: Name of the strategy that failed
            error: Error message from failed extraction

        Returns:
            Dict[str, Any]: Fallback metadata
        """
        fallback_metadata = {
            "extraction_method": f"{strategy_name}_fallback",
            "page_count": 0,
            "title": path.stem,
            "author": "unknown",
            "subject": "unknown",
            "creator": "unknown",
            "producer": "unknown",
            "error": error
        }

        # Add file statistics if possible
        try:
            file_stats = path.stat()
            fallback_metadata.update({
                "file_modified": file_stats.st_mtime,
                "file_name": path.name
            })
        except OSError:
            pass

        return fallback_metadata

    def _get_strategy_factory_info(self) -> Dict[str, Any]:
        """
        Get information about the current strategy factory state.

        Returns:
            Dict[str, Any]: Factory information for debugging
        """
        try:
            factory = get_pdf_strategy_factory()
            return factory.get_factory_stats()
        except Exception as e:
            logger.warning(f"Failed to get strategy factory info: {e}")
            return {"error": str(e)}

    async def get_loader_status(self) -> Dict[str, Any]:
        """
        Get current loader status and configuration.

        Returns:
            Dict[str, Any]: Loader status information
        """
        factory_info = self._get_strategy_factory_info()
        
        return {
            "loader_name": self.loader_name,
            "supported_formats": self.supported_formats(),
            "config": {
                "default_strategy": self.config.default_strategy,
                "max_file_size": self.config.max_file_size,
                "enable_fallback": self.config.enable_fallback,
                "strategy_count": factory_info.get("total_strategies", 0)
            },
            "factory_info": factory_info
        }

    def __str__(self) -> str:
        """String representation of the loader."""
        return (
            f"PDFFileLoader(strategy={self.config.default_strategy}, "
            f"max_size={self.config.max_file_size}, "
            f"fallback={self.config.enable_fallback})"
        )

    def __repr__(self) -> str:
        """Detailed representation of the loader."""
        return (
            f"PDFFileLoader(config={self.config}, "
            f"supported_formats={self._supported_formats})"
        )