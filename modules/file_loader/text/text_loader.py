"""
Text file loader

Specialized loader for handling plain text files.
Supports multiple encoding formats and error handling.
"""

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from modules.file_loader import (
    FileLoaderError,
    IFileLoader,
    register_multi_type_file_loader,
)
from modules.schemas import ContentType, Document, create_document_from_path

logger = logging.getLogger(__name__)


try:
    import chardet

    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False
    chardet = None


@register_multi_type_file_loader(content_types=[ContentType.TXT])
class TextFileLoader(IFileLoader):
    """Text file loader"""

    def __init__(
        self,
        default_encoding: str = "utf-8",
        fallback_encodings: list = None,
        max_file_size: int = 100 * 1024 * 1024,
    ):  # 100MB
        """
        Initialize text file loader

        Args:
            default_encoding: Default encoding
            fallback_encodings: List of fallback encodings
            max_file_size: Maximum file size in bytes
        """
        self.default_encoding = default_encoding
        self.fallback_encodings = fallback_encodings or [
            "gbk",
            "gb2312",
            "latin1",
            "ascii",
        ]
        self.max_file_size = max_file_size

        logger.info(
            f"TextFileLoader initialized: default_encoding={default_encoding}, max_file_size={max_file_size / 1024 / 1024:.1f}MB"
        )

    @property
    def loader_name(self) -> str:
        """Get loader name"""
        return "TextFileLoader"

    def supported_formats(self) -> list:
        """Get supported file formats"""
        return [".txt", ".md", ".markdown", ".csv", ".log", ".ini", ".cfg", ".conf"]

    def supported_types(self) -> list:
        """Get supported content types (interface method)"""
        return [ContentType.TXT]

    def supports_content_type(self, content_type: ContentType) -> bool:
        """Check if the specified content type is supported"""
        return content_type in self.supported_types()

    async def validate_file(self, file_path: str) -> bool:
        """Validate if file can be loaded (interface method)"""
        return await self.can_load(file_path)

    async def can_load(self, file_path: str) -> bool:
        """Check if the specified file can be loaded"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.warning(
                    f"File too large: {file_path} ({file_size / 1024 / 1024:.1f}MB)"
                )
                return False

            # Check file extension
            _, ext = os.path.splitext(file_path.lower())
            if ext in self.supported_formats():
                return True

            # Try to read file header to determine if it's a text file
            try:
                with open(file_path, "rb") as f:
                    sample = f.read(1024)

                # Check if it contains too much binary data
                if sample:
                    # Calculate proportion of non-ASCII characters
                    non_text_chars = sum(
                        1 for byte in sample if byte < 32 and byte not in [9, 10, 13]
                    )
                    if (
                        non_text_chars / len(sample) > 0.3
                    ):  # More than 30% non-text characters
                        return False

                return True

            except Exception as e:
                logger.debug(f"Failed to check file type {file_path}: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to check file loadability {file_path}: {e}")
            return False

    async def load_document(self, request) -> Document:
        """Load document (interface method)"""
        from ..models import FileLoadRequest

        # If a path string is passed in, convert to request object
        if isinstance(request, str):
            file_path = request
            metadata = {}
        elif isinstance(request, FileLoadRequest):
            file_path = request.file_path
            metadata = request.metadata or {}
        else:
            file_path = request
            metadata = {}

        return await self.load_file(file_path, metadata)

    async def load_file(
        self, file_path: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Load text file"""
        try:
            # Validate file
            if not await self.can_load(file_path):
                raise FileLoaderError(f"Cannot load file: {file_path}")

            # Detect encoding
            encoding = await self._detect_encoding(file_path)

            # Read file content
            content = await self._read_file_content(file_path, encoding)

            # Create document object
            document = create_document_from_path(file_path, content)

            # Add metadata
            document.metadata.update(
                {
                    "loader": self.loader_name,
                    "encoding": encoding,
                    "file_size": len(content.encode("utf-8")),
                    "char_count": len(content),
                    "line_count": len(content.splitlines()),
                    "has_chardet": HAS_CHARDET,
                    **(metadata or {}),
                }
            )

            logger.info(
                f"Successfully loaded text file: {file_path} ({len(content)} characters, encoding: {encoding})"
            )
            return document

        except FileLoaderError:
            raise
        except Exception as e:
            logger.error(f"Failed to load text file {file_path}: {e}")
            raise FileLoaderError(f"Failed to load text file: {str(e)}")

    async def _detect_encoding(self, file_path: str) -> str:
        """Detect file encoding"""
        try:
            if HAS_CHARDET:
                # Use chardet to detect encoding
                with open(file_path, "rb") as f:
                    sample = f.read(10240)  # Read first 10KB sample
                    if sample:
                        detection = chardet.detect(sample)

                        if detection and detection.get("confidence", 0) > 0.7:
                            detected_encoding = detection["encoding"]
                            logger.debug(
                                f"Detected encoding: {detected_encoding} (confidence: {detection.get('confidence', 0):.2f})"
                            )
                            return detected_encoding
            else:
                # Use basic detection method when chardet is not available
                with open(file_path, "rb") as f:
                    sample = f.read(1000)
                    if sample:
                        # Simple UTF-8 detection
                        try:
                            sample.decode("utf-8")
                            logger.debug("Detected encoding: utf-8 (basic detection)")
                            return "utf-8"
                        except UnicodeDecodeError:
                            pass

                        # Detect common encodings
                        for encoding in self.fallback_encodings:
                            try:
                                sample.decode(encoding)
                                logger.debug(
                                    f"Detected encoding: {encoding} (basic detection)"
                                )
                                return encoding
                            except UnicodeDecodeError:
                                continue

            # Fall back to default encoding
            logger.warning(
                f"Cannot detect encoding, using default encoding: {self.default_encoding}"
            )
            return self.default_encoding

        except Exception as e:
            logger.warning(f"Encoding detection failed {file_path}: {e}")
            return self.default_encoding

    async def _read_file_content(self, file_path: str, encoding: str) -> str:
        """Read file content"""
        try:
            # Read file asynchronously
            def read_sync():
                with open(file_path, "r", encoding=encoding, errors="replace") as f:
                    return f.read()

            # Execute file reading in thread pool
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, read_sync)

            return content

        except Exception as e:
            # If specified encoding fails, try fallback encodings
            logger.warning(
                f"Failed to read with encoding {encoding}, trying fallback encodings: {e}"
            )

            for fallback_encoding in self.fallback_encodings:
                try:

                    def read_fallback():
                        with open(
                            file_path, "r", encoding=fallback_encoding, errors="replace"
                        ) as f:
                            return f.read()

                    loop = asyncio.get_event_loop()
                    content = await loop.run_in_executor(None, read_fallback)

                    logger.info(
                        f"Successfully read file using fallback encoding {fallback_encoding}"
                    )
                    return content

                except Exception as fallback_error:
                    logger.debug(
                        f"Fallback encoding {fallback_encoding} also failed: {fallback_error}"
                    )
                    continue

            # All encodings failed, raise exception
            raise FileLoaderError(f"Cannot read file with any encoding: {file_path}")

    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        return {
            "loader_name": self.loader_name,
            "status": "healthy",
            "supported_formats": self.supported_formats(),
            "default_encoding": self.default_encoding,
            "max_file_size_mb": self.max_file_size / 1024 / 1024,
            "has_chardet": HAS_CHARDET,
            "fallback_encodings": self.fallback_encodings,
        }
