"""Document parser factory with registry pattern.

This module provides a factory for creating document parsers based on MIME type
or file extension. New parsers can be registered to extend format support.

The factory also supports switching OCR providers via the `ocr_provider` setting:
- "docling": Uses Docling for document parsing (default)
- "gemini": Uses Google Gemini Vision for PDF OCR
"""

from typing import Dict, List, Optional, Type

from research_agent.config import get_settings
from research_agent.infrastructure.parser.base import (
    DocumentParser,
    DocumentParsingError,
)
from research_agent.infrastructure.parser.docling_parser import DoclingParser
from research_agent.shared.utils.logger import logger

# Lazy import for GeminiParser to avoid loading google-generativeai if not needed
_gemini_parser_instance: Optional[DocumentParser] = None


def _get_gemini_parser() -> DocumentParser:
    """Get or create a GeminiParser instance (lazy loading)."""
    global _gemini_parser_instance
    if _gemini_parser_instance is None:
        from research_agent.infrastructure.parser.gemini_parser import GeminiParser

        _gemini_parser_instance = GeminiParser()
        logger.info("GeminiParser initialized for OCR")
    return _gemini_parser_instance


def _is_pdf_format(mime_type: Optional[str], extension: Optional[str]) -> bool:
    """Check if the format is PDF."""
    if mime_type == "application/pdf":
        return True
    if extension:
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        if ext == ".pdf":
            return True
    return False


class ParserRegistry:
    """
    Registry for document parsers.

    Maintains a mapping of MIME types and extensions to parser classes,
    allowing dynamic registration of new parsers.
    """

    def __init__(self):
        self._mime_parsers: Dict[str, Type[DocumentParser]] = {}
        self._extension_parsers: Dict[str, Type[DocumentParser]] = {}
        self._parser_instances: Dict[str, DocumentParser] = {}

    def register(self, parser_class: Type[DocumentParser]) -> None:
        """
        Register a parser class for its supported formats.

        Args:
            parser_class: Parser class to register.
        """
        # Create a temporary instance to get supported formats
        temp_instance = parser_class()

        for mime_type in temp_instance.supported_formats():
            self._mime_parsers[mime_type] = parser_class
            logger.debug(f"Registered parser {parser_class.__name__} for MIME: {mime_type}")

        for extension in temp_instance.supported_extensions():
            ext = extension.lower()
            if not ext.startswith("."):
                ext = f".{ext}"
            self._extension_parsers[ext] = parser_class
            logger.debug(f"Registered parser {parser_class.__name__} for extension: {ext}")

    def get_parser_class(
        self, mime_type: Optional[str] = None, extension: Optional[str] = None
    ) -> Optional[Type[DocumentParser]]:
        """
        Get parser class for given MIME type or extension.

        Args:
            mime_type: MIME type string.
            extension: File extension (with or without leading dot).

        Returns:
            Parser class if found, None otherwise.
        """
        if mime_type and mime_type in self._mime_parsers:
            return self._mime_parsers[mime_type]

        if extension:
            ext = extension.lower()
            if not ext.startswith("."):
                ext = f".{ext}"
            if ext in self._extension_parsers:
                return self._extension_parsers[ext]

        return None

    def get_parser(
        self, mime_type: Optional[str] = None, extension: Optional[str] = None
    ) -> Optional[DocumentParser]:
        """
        Get or create a parser instance for given MIME type or extension.

        Args:
            mime_type: MIME type string.
            extension: File extension.

        Returns:
            Parser instance if found, None otherwise.
        """
        parser_class = self.get_parser_class(mime_type, extension)
        if parser_class is None:
            return None

        # Cache parser instances
        class_name = parser_class.__name__
        if class_name not in self._parser_instances:
            self._parser_instances[class_name] = parser_class()

        return self._parser_instances[class_name]

    def supported_mime_types(self) -> List[str]:
        """Return all supported MIME types."""
        return list(self._mime_parsers.keys())

    def supported_extensions(self) -> List[str]:
        """Return all supported file extensions."""
        return list(self._extension_parsers.keys())

    def is_supported(
        self, mime_type: Optional[str] = None, extension: Optional[str] = None
    ) -> bool:
        """
        Check if a format is supported.

        Args:
            mime_type: MIME type string.
            extension: File extension.

        Returns:
            True if format is supported.
        """
        return self.get_parser_class(mime_type, extension) is not None


# Global registry instance
_registry = ParserRegistry()


def _initialize_default_parsers():
    """Register default parsers."""
    # Register Docling parser for PDF/Word/PPT
    _registry.register(DoclingParser)
    logger.info("Default document parsers registered")


# Initialize on module load
_initialize_default_parsers()


class ParserFactory:
    """
    Factory for creating document parsers.

    Uses the global registry to find appropriate parsers for given formats.
    """

    @staticmethod
    def get_parser(
        mime_type: Optional[str] = None, extension: Optional[str] = None
    ) -> DocumentParser:
        """
        Get a parser for the given MIME type or extension.

        The parser selection considers the `ocr_provider` setting:
        - If ocr_provider is "gemini" and format is PDF, returns GeminiParser.
        - Otherwise, returns the default parser from the registry (Docling).

        Args:
            mime_type: MIME type string (e.g., "application/pdf").
            extension: File extension (e.g., ".pdf" or "pdf").

        Returns:
            Appropriate DocumentParser instance.

        Raises:
            DocumentParsingError: If no parser found for the format.
        """
        settings = get_settings()

        # Check if we should use Gemini for PDF OCR
        if settings.ocr_provider == "gemini" and _is_pdf_format(mime_type, extension):
            if not settings.google_api_key:
                logger.warning(
                    "ocr_provider is 'gemini' but GOOGLE_API_KEY is not set. "
                    "Falling back to Docling parser."
                )
            else:
                logger.debug("Using GeminiParser for PDF OCR")
                return _get_gemini_parser()

        # Use default registry-based parser
        parser = _registry.get_parser(mime_type, extension)
        if parser is None:
            raise DocumentParsingError(
                f"No parser available for mime_type={mime_type}, extension={extension}. "
                f"Supported MIME types: {_registry.supported_mime_types()}"
            )
        return parser

    @staticmethod
    def is_supported(mime_type: Optional[str] = None, extension: Optional[str] = None) -> bool:
        """
        Check if a format is supported.

        Args:
            mime_type: MIME type string.
            extension: File extension.

        Returns:
            True if format is supported by any registered parser.
        """
        return _registry.is_supported(mime_type, extension)

    @staticmethod
    def supported_mime_types() -> List[str]:
        """Return all supported MIME types."""
        return _registry.supported_mime_types()

    @staticmethod
    def supported_extensions() -> List[str]:
        """Return all supported file extensions."""
        return _registry.supported_extensions()

    @staticmethod
    def register_parser(parser_class: Type[DocumentParser]) -> None:
        """
        Register a new parser class.

        This allows extending format support without modifying the factory.

        Args:
            parser_class: Parser class to register.
        """
        _registry.register(parser_class)
        logger.info(f"Registered new parser: {parser_class.__name__}")
