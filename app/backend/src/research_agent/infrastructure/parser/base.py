"""Document parser abstract interface.

This module defines the base interface for all document parsers, supporting
multiple formats including PDF, Word, PPT, and Audio/Video files.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    AUDIO = "audio"
    VIDEO = "video"
    UNKNOWN = "unknown"


@dataclass
class ParsedPage:
    """
    Parsed page/segment data class.

    For text documents (PDF, Word, PPT): represents a page.
    For audio/video: represents a time segment or chapter.
    """

    page_number: int
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Optional fields for different document types
    # Audio/Video specific
    start_time: Optional[float] = None  # Start time in seconds
    end_time: Optional[float] = None  # End time in seconds
    speaker: Optional[str] = None  # Speaker identification

    # OCR specific
    ocr_confidence: Optional[float] = None  # OCR confidence score (0-1)
    has_ocr: bool = False  # Whether OCR was applied

    # Layout specific
    layout_type: Optional[str] = None  # e.g., "single_column", "multi_column", "table"


@dataclass
class ParseResult:
    """
    Complete parsing result containing all pages and document-level metadata.
    """

    pages: List[ParsedPage]
    document_type: DocumentType
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Document-level properties
    page_count: int = 0
    total_duration: Optional[float] = None  # For audio/video, duration in seconds
    has_ocr: bool = False  # Whether any page required OCR
    parser_name: str = ""  # Name of parser used

    def __post_init__(self):
        if self.page_count == 0:
            self.page_count = len(self.pages)


class DocumentParser(ABC):
    """
    Abstract document parser interface.

    All format-specific parsers should inherit from this class and implement
    the required methods. This enables a pluggable architecture where new
    format support can be added without modifying the core processing logic.
    """

    @abstractmethod
    async def parse(self, file_path: str) -> ParseResult:
        """
        Parse a document file and extract structured content.

        Args:
            file_path: Path to the document file.

        Returns:
            ParseResult containing pages and metadata.

        Raises:
            DocumentParsingError: If parsing fails.
        """
        pass

    @abstractmethod
    def supported_formats(self) -> List[str]:
        """
        Return list of supported MIME types.

        Returns:
            List of MIME type strings this parser can handle.
        """
        pass

    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """
        Return list of supported file extensions.

        Returns:
            List of file extension strings (e.g., [".pdf", ".docx"]).
        """
        pass

    def can_handle(self, mime_type: str) -> bool:
        """
        Check if this parser can handle the given MIME type.

        Args:
            mime_type: MIME type string to check.

        Returns:
            True if this parser supports the MIME type.
        """
        return mime_type in self.supported_formats()

    def can_handle_extension(self, extension: str) -> bool:
        """
        Check if this parser can handle the given file extension.

        Args:
            extension: File extension to check (with or without leading dot).

        Returns:
            True if this parser supports the extension.
        """
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext in self.supported_extensions()

    @property
    def parser_name(self) -> str:
        """Return the name of this parser for logging/debugging."""
        return self.__class__.__name__


class DocumentParsingError(Exception):
    """Exception raised when document parsing fails."""

    def __init__(self, message: str, file_path: str = "", cause: Exception = None):
        self.file_path = file_path
        self.cause = cause
        super().__init__(message)
