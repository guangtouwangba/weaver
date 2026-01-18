"""Document parser factory with registry pattern.

This module provides a factory for creating document parsers based on MIME type
or file extension. New parsers can be registered to extend format support.

Default parsers:
- PDF: PyMuPDF (lightweight, no system deps)
- DOCX/PPTX: Unstructured (no [pdf] extra to avoid cv2/libGL)

The factory supports multiple OCR modes via the `ocr_mode` setting:
- "auto": Smart mode - uses PyMuPDF first, auto-switches to Gemini OCR for scanned PDFs
- "docling": Uses Docling for document parsing (requires PyTorch, optional install)
- "gemini": Always uses Google Gemini Vision for PDF OCR
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Type

from research_agent.config import get_settings
from research_agent.infrastructure.parser.base import (
    DocumentParser,
    DocumentParsingError,
)
from research_agent.infrastructure.parser.pymupdf_parser import PyMuPDFDocumentParser
from research_agent.infrastructure.parser.unstructured_parser import UnstructuredParser
from research_agent.shared.utils.logger import logger

if TYPE_CHECKING:
    from research_agent.infrastructure.parser.base import ParseResult

# Lazy imports for optional parsers to avoid loading heavy dependencies
_gemini_parser_instance: Optional[DocumentParser] = None
_docling_parser_instance: Optional[DocumentParser] = None
_modal_parser_instance: Optional[DocumentParser] = None


def _get_gemini_parser() -> DocumentParser:
    """Get or create a GeminiParser instance (lazy loading)."""
    global _gemini_parser_instance
    if _gemini_parser_instance is None:
        from research_agent.infrastructure.parser.gemini_parser import GeminiParser

        _gemini_parser_instance = GeminiParser()
        logger.info("GeminiParser initialized for OCR")
    return _gemini_parser_instance


def _get_docling_parser() -> DocumentParser:
    """Get or create a DoclingParser instance (lazy loading).

    Note: Docling requires PyTorch and is ~2-5GB. Only use if explicitly configured.
    """
    global _docling_parser_instance
    if _docling_parser_instance is None:
        try:
            from research_agent.infrastructure.parser.docling_parser import DoclingParser

            _docling_parser_instance = DoclingParser()
            logger.info("DoclingParser initialized (with PyTorch)")
        except ImportError as e:
            raise DocumentParsingError(
                "Docling not installed. Install with: pip install 'research-agent-rag[ocr]'",
                cause=e,
            )
    return _docling_parser_instance


def _get_modal_parser() -> DocumentParser:
    """Get or create a ModalParser instance (lazy loading).

    Note: ModalParser uses Modal serverless infrastructure for GPU-accelerated OCR.
    Requires Modal to be configured and the OCR app to be deployed.
    """
    global _modal_parser_instance
    if _modal_parser_instance is None:
        try:
            from research_agent.infrastructure.parser.modal_parser import ModalParser

            _modal_parser_instance = ModalParser()
            logger.info("ModalParser initialized for GPU-accelerated OCR")
        except ImportError as e:
            raise DocumentParsingError(
                "Modal not installed. Install with: pip install modal",
                cause=e,
            )
        except Exception as e:
            raise DocumentParsingError(
                f"Failed to initialize ModalParser: {e}. "
                "Ensure Modal is configured with valid credentials. "
                "Run 'modal token new' to authenticate.",
                cause=e,
            )
    return _modal_parser_instance


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
    from research_agent.infrastructure.parser.text_parser import TextParser

    # Register PyMuPDF for PDF (lightweight, no system deps like libGL)
    _registry.register(PyMuPDFDocumentParser)
    # Register Unstructured for Word/PPT (no [pdf] extra to avoid cv2/libGL)
    _registry.register(UnstructuredParser)
    # Register TextParser for plain text files
    _registry.register(TextParser)
    logger.info(
        "Default document parsers registered (PyMuPDF for PDF, Unstructured for DOCX/PPTX, TextParser for TXT)"
    )


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

        The parser selection considers the `ocr_mode` setting:
        - If ocr_mode is "gemini" and format is PDF, returns GeminiParser.
        - If ocr_mode is "docling", returns DoclingParser (requires PyTorch).
        - Otherwise, returns the default parser from the registry (Unstructured).

        Note: For "auto" mode, use `parse_with_auto_ocr()` instead.

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
        if settings.ocr_mode == "gemini" and _is_pdf_format(mime_type, extension):
            if not settings.google_api_key:
                logger.warning(
                    "ocr_mode is 'gemini' but GOOGLE_API_KEY is not set. "
                    "Falling back to default parser."
                )
            else:
                logger.debug("Using GeminiParser for PDF OCR")
                return _get_gemini_parser()

        # Check if we should use Docling (heavy, with PyTorch)
        if settings.ocr_mode == "docling":
            logger.debug("Using DoclingParser (with PyTorch)")
            return _get_docling_parser()

        # Use default registry-based parser (Unstructured - lightweight)
        parser = _registry.get_parser(mime_type, extension)
        if parser is None:
            raise DocumentParsingError(
                f"No parser available for mime_type={mime_type}, extension={extension}. "
                f"Supported MIME types: {_registry.supported_mime_types()}"
            )
        return parser

    @staticmethod
    async def parse_with_auto_ocr(
        file_path: str,
        mime_type: Optional[str] = None,
        extension: Optional[str] = None,
    ) -> "ParseResult":
        """
        Smart parsing with automatic OCR fallback for scanned PDFs.

        This method first attempts to parse with Unstructured (lightweight).
        If the result indicates a scanned PDF (too few characters or too much
        garbage), it automatically retries with Gemini Vision OCR.

        Args:
            file_path: Path to the document file.
            mime_type: MIME type string (e.g., "application/pdf").
            extension: File extension (e.g., ".pdf" or "pdf").

        Returns:
            ParseResult from the appropriate parser.

        Raises:
            DocumentParsingError: If parsing fails with all methods.
        """
        from research_agent.infrastructure.parser.utils import is_scanned_pdf

        settings = get_settings()
        is_pdf = _is_pdf_format(mime_type, extension)

        logger.info(f"[SmartOCR] Starting auto-detection for: {file_path}")

        # Step 1: Choose parser based on file type
        # - PDF: Use PyMuPDF (lightweight, no system deps)
        # - Other formats: Use registry to find appropriate parser
        if is_pdf:
            default_parser = PyMuPDFDocumentParser()
            logger.debug("[SmartOCR] Using PyMuPDF for PDF")
        else:
            # Use registry to get the best parser for this file type
            default_parser = _registry.get_parser(mime_type, extension)
            if default_parser is None:
                default_parser = UnstructuredParser()
                logger.debug("[SmartOCR] No registered parser found, using Unstructured")
            else:
                logger.debug(f"[SmartOCR] Using {default_parser.parser_name} for {extension}")

        try:
            result = await default_parser.parse(file_path)
        except Exception as e:
            logger.warning(f"[SmartOCR] Primary parser failed: {e}")
            # If primary parser fails, try Gemini for PDFs if available
            if is_pdf and settings.google_api_key:
                logger.info("[SmartOCR] Falling back to Gemini OCR due to parsing failure")
                try:
                    gemini_parser = _get_gemini_parser()
                    return await gemini_parser.parse(file_path)
                except DocumentParsingError as gemini_error:
                    error_str = str(gemini_error).lower()
                    is_network_error = (
                        "network" in error_str
                        or "connect" in error_str
                        or "timeout" in error_str
                        or "reach" in error_str
                    )
                    if is_network_error:
                        logger.error(
                            f"[SmartOCR] ⚠️ Gemini OCR also failed due to network issue: {gemini_error}"
                        )
                        logger.error(
                            "[SmartOCR] 💡 Both parsers failed. Check network connectivity to Google APIs."
                        )
                    # Re-raise the original error since both parsers failed
                    raise e from gemini_error
            raise

        # Step 2: For PDFs, check if it's scanned and needs OCR
        if is_pdf:
            needs_ocr = is_scanned_pdf(
                result,
                min_chars_per_page=settings.ocr_min_chars_per_page,
                max_garbage_ratio=settings.ocr_max_garbage_ratio,
            )

            if needs_ocr:
                if not settings.google_api_key:
                    logger.warning(
                        "[SmartOCR] Scanned PDF detected but GOOGLE_API_KEY not set. "
                        "Using PyMuPDF result (may be low quality)."
                    )
                    return result

                logger.info("[SmartOCR] Scanned PDF detected, switching to Gemini OCR")
                try:
                    gemini_parser = _get_gemini_parser()
                    result = await gemini_parser.parse(file_path)
                    logger.info("[SmartOCR] Gemini OCR completed successfully")
                except DocumentParsingError as e:
                    error_str = str(e).lower()
                    # Check if it's a network/connectivity error
                    is_network_error = (
                        "network" in error_str
                        or "connect" in error_str
                        or "timeout" in error_str
                        or "reach" in error_str
                    )
                    if is_network_error:
                        logger.warning(f"[SmartOCR] ⚠️ Gemini OCR failed due to network issue: {e}")
                        logger.warning(
                            "[SmartOCR] 💡 Falling back to PyMuPDF result. "
                            "For better results with scanned PDFs, ensure network access to Google APIs "
                            "or set OCR_MODE=unstructured in .env"
                        )
                        # Return the original PyMuPDF result (low quality but better than nothing)
                        return result
                    else:
                        # Non-network error, re-raise
                        raise

        return result

    @staticmethod
    async def parse_with_mode(
        file_path: str,
        mode: str,
        mime_type: Optional[str] = None,
        extension: Optional[str] = None,
    ) -> "ParseResult":
        """
        Parse document with specified processing mode.

        This method provides a user-friendly abstraction over different parsing strategies:
        - "fast": Quick text extraction, no OCR. Best for text-based documents.
        - "standard": Auto-detects scanned documents and applies OCR when needed (Gemini).
        - "quality": GPU-accelerated OCR with structure preservation (Modal + Marker).

        Args:
            file_path: Path to the document file.
            mode: Processing mode ("fast", "standard", "quality").
            mime_type: MIME type string (e.g., "application/pdf").
            extension: File extension (e.g., ".pdf" or "pdf").

        Returns:
            ParseResult from the appropriate parser.

        Raises:
            DocumentParsingError: If parsing fails.
            ValueError: If mode is invalid.
        """
        valid_modes = ["fast", "standard", "quality"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid processing mode: {mode}. Valid modes: {valid_modes}")

        logger.info(f"[ParseWithMode] Processing '{file_path}' with mode='{mode}'")

        is_pdf = _is_pdf_format(mime_type, extension)

        # FAST MODE: Quick text extraction, no OCR fallback
        if mode == "fast":
            logger.info("[ParseWithMode] Fast mode - using basic text extraction only")
            if is_pdf:
                parser = PyMuPDFDocumentParser()
            else:
                # Use registry to get the best parser for this file type
                parser = _registry.get_parser(mime_type, extension)
                if parser is None:
                    parser = UnstructuredParser()
                    logger.debug("[ParseWithMode] No registered parser, using Unstructured")
                else:
                    logger.debug(f"[ParseWithMode] Using {parser.parser_name} for {extension}")
            return await parser.parse(file_path)

        # STANDARD MODE: Auto-detect + Gemini OCR fallback
        if mode == "standard":
            logger.info("[ParseWithMode] Standard mode - auto-detection with Gemini fallback")
            return await ParserFactory.parse_with_auto_ocr(
                file_path=file_path,
                mime_type=mime_type,
                extension=extension,
            )

        # QUALITY MODE: GPU-accelerated OCR with Modal + Marker
        if mode == "quality":
            logger.info("[ParseWithMode] Quality mode - using Modal + Marker GPU OCR")
            # Check if file type is supported by Modal (PDF and images)
            is_image = extension and extension.lower() in [".jpg", ".jpeg", ".png", ".webp"]
            if is_pdf or is_image:
                try:
                    modal_parser = _get_modal_parser()
                    return await modal_parser.parse(file_path)
                except DocumentParsingError as e:
                    # Log warning and fall back to standard mode
                    logger.warning(
                        f"[ParseWithMode] Modal OCR failed: {e}. Falling back to standard mode."
                    )
                    return await ParserFactory.parse_with_auto_ocr(
                        file_path=file_path,
                        mime_type=mime_type,
                        extension=extension,
                    )
            else:
                # For non-PDF/image formats, use registry to find appropriate parser
                parser = _registry.get_parser(mime_type, extension)
                if parser is None:
                    parser = UnstructuredParser()
                    logger.info(
                        f"[ParseWithMode] Quality mode not applicable for extension '{extension}', "
                        "using Unstructured parser"
                    )
                else:
                    logger.info(
                        f"[ParseWithMode] Quality mode not applicable for extension '{extension}', "
                        f"using {parser.parser_name}"
                    )
                return await parser.parse(file_path)

        # Should not reach here due to validation above
        raise ValueError(f"Unhandled processing mode: {mode}")

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
