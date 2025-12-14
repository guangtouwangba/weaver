"""Modal-based document parser for serverless GPU-accelerated OCR.

This parser delegates document parsing to Modal's serverless infrastructure,
providing GPU-accelerated OCR with automatic scaling and parallel processing
for large documents.
"""

import asyncio
from pathlib import Path
from typing import List, Optional

from research_agent.config import get_settings
from research_agent.infrastructure.parser.base import (
    DocumentParser,
    DocumentParsingError,
    DocumentType,
    ParsedPage,
    ParseResult,
)
from research_agent.shared.utils.logger import logger


class ModalParser(DocumentParser):
    """
    Modal-based document parser using Marker library on GPU.

    Features:
    - GPU-accelerated OCR via Modal serverless
    - Automatic parallel processing for large documents (>50 pages)
    - No local GPU/PyTorch dependencies required
    - Auto-scaling: 0 to N instances based on demand

    Configuration:
    - Requires MODAL_TOKEN_ID and MODAL_TOKEN_SECRET environment variables
    - Or run `modal token new` to authenticate locally

    Usage:
        parser = ModalParser()
        result = await parser.parse("/path/to/document.pdf")
    """

    # Supported formats (PDF and images for OCR)
    SUPPORTED_MIME_TYPES = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    ]

    SUPPORTED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".webp"]

    # Modal app configuration
    MODAL_APP_NAME = "research-agent-ocr"
    MODAL_FUNCTION_NAME = "parse_document"

    def __init__(
        self,
        output_format: str = "markdown",
        force_ocr: bool = False,
        timeout: int = 900,
    ):
        """Initialize the Modal parser.

        Args:
            output_format: Output format ("markdown", "html", or "json").
            force_ocr: Force OCR even for text PDFs.
            timeout: Timeout in seconds for Modal function calls.
        """
        self.output_format = output_format
        self.force_ocr = force_ocr
        self.timeout = timeout
        self._function = None

    def _get_modal_function(self):
        """Get or create the Modal function reference.

        Lazy initialization to avoid import errors when Modal is not installed.
        """
        if self._function is None:
            try:
                import modal

                settings = get_settings()

                # Use custom app name if configured
                app_name = getattr(settings, "modal_app_name", None) or self.MODAL_APP_NAME

                logger.info(f"Connecting to Modal app: {app_name}")
                self._function = modal.Function.from_name(
                    app_name,
                    self.MODAL_FUNCTION_NAME,
                )
                logger.info("Modal function reference created successfully")

            except ImportError as e:
                raise DocumentParsingError(
                    "Modal library not installed. Install with: pip install modal",
                    cause=e,
                )
            except Exception as e:
                raise DocumentParsingError(
                    f"Failed to connect to Modal service: {e}. "
                    "Ensure Modal is configured with valid credentials. "
                    "Run 'modal token new' to authenticate.",
                    cause=e,
                )

        return self._function

    def supported_formats(self) -> List[str]:
        """Return list of supported MIME types."""
        return self.SUPPORTED_MIME_TYPES.copy()

    def supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()

    async def parse(self, file_path: str) -> ParseResult:
        """Parse a document using Modal serverless OCR.

        Args:
            file_path: Path to the document file.

        Returns:
            ParseResult containing parsed pages and metadata.

        Raises:
            DocumentParsingError: If parsing fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentParsingError(f"File not found: {file_path}", file_path=file_path)

        logger.info(f"Parsing document with Modal OCR: {file_path}")

        try:
            # Read file content
            document_bytes = path.read_bytes()
            file_size_mb = len(document_bytes) / (1024 * 1024)
            logger.info(f"Document size: {file_size_mb:.2f} MB")

            # Validate file size (Modal limit is 512MB)
            if file_size_mb > 500:
                raise DocumentParsingError(
                    f"Document too large ({file_size_mb:.2f} MB). Modal supports up to 512MB.",
                    file_path=file_path,
                )

            # Call Modal function
            result = await self._call_modal(document_bytes)

            # Check for errors
            if result.get("error"):
                raise DocumentParsingError(
                    f"Modal OCR failed: {result['error']}",
                    file_path=file_path,
                )

            # Log result details for debugging
            content = result.get("content", "")
            content_len = len(content) if content else 0
            logger.info(
                f"Modal result - content_length={content_len}, "
                f"page_count={result.get('page_count', 0)}, "
                f"processing_mode={result.get('processing_mode', 'unknown')}, "
                f"has_ocr={result.get('has_ocr', False)}"
            )

            # Warn if content is empty (OCR might have failed silently)
            if not content or content_len == 0:
                logger.warning(
                    f"⚠️ Modal OCR returned empty content for {file_path}. "
                    f"This may indicate OCR extraction failed. Result: {result}"
                )

            # Convert result to ParseResult
            parse_result = self._convert_to_parse_result(result, path)

            logger.info(
                f"Modal OCR complete: {parse_result.page_count} pages, "
                f"mode={result.get('processing_mode', 'unknown')}, "
                f"chunks={result.get('chunks_processed', 1)}"
            )

            return parse_result

        except DocumentParsingError:
            raise
        except Exception as e:
            logger.error(f"Modal OCR failed for {file_path}: {e}", exc_info=True)
            raise DocumentParsingError(
                f"Failed to parse document with Modal: {e}",
                file_path=file_path,
                cause=e,
            )

    async def _call_modal(self, document_bytes: bytes) -> dict:
        """Call the Modal function to parse the document.

        Args:
            document_bytes: Document content as bytes.

        Returns:
            Dict with parsing results.
        """
        fn = self._get_modal_function()

        # Modal's .remote() is synchronous, run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: fn.remote(
                document=document_bytes,
                output_format=self.output_format,
                force_ocr=self.force_ocr,
            ),
        )

        return result

    def _convert_to_parse_result(self, result: dict, path: Path) -> ParseResult:
        """Convert Modal result to ParseResult format.

        Args:
            result: Result dict from Modal function.
            path: Original file path.

        Returns:
            ParseResult object.
        """
        content = result.get("content", "")
        page_count = result.get("page_count", 1)
        has_ocr = result.get("has_ocr", True)

        # Split content into pages based on page separators
        pages = self._split_content_to_pages(content, page_count)

        # Determine document type from extension
        extension = path.suffix.lower()
        doc_type = self._get_document_type(extension)

        return ParseResult(
            pages=pages,
            document_type=doc_type,
            metadata={
                "source_file": path.name,
                "file_extension": extension,
                "processing_mode": result.get("processing_mode", "unknown"),
                "chunks_processed": result.get("chunks_processed", 1),
                "parser": "modal_marker",
            },
            page_count=page_count,
            has_ocr=has_ocr,
            parser_name=self.parser_name,
        )

    def _split_content_to_pages(
        self,
        content: str,
        expected_page_count: int,
    ) -> List[ParsedPage]:
        """Split parsed content into individual pages.

        Marker uses page markers in paginated output.
        Format: \\n\\n{PAGE_NUMBER}\\n------------------------------------------------\\n\\n

        Args:
            content: Full parsed content.
            expected_page_count: Expected number of pages.

        Returns:
            List of ParsedPage objects.
        """
        if not content:
            return [ParsedPage(page_number=1, content="", metadata={})]

        # Try to split by Marker's page separators
        import re

        # Marker page separator pattern
        page_pattern = r"\n\n(\d+)\n-{48}\n\n"
        parts = re.split(page_pattern, content)

        pages = []
        if len(parts) > 1:
            # First part is content before first page marker (usually empty)
            # Then alternating: page_number, content, page_number, content, ...
            current_content = parts[0].strip()
            if current_content:
                pages.append(
                    ParsedPage(
                        page_number=1,
                        content=current_content,
                        metadata={"extraction_method": "page_split"},
                    )
                )

            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    page_num = int(parts[i])
                    page_content = parts[i + 1].strip()
                    pages.append(
                        ParsedPage(
                            page_number=page_num,
                            content=page_content,
                            metadata={"extraction_method": "page_split"},
                        )
                    )
        else:
            # No page markers found, treat as single page or split by double newlines
            if expected_page_count > 1:
                # Try splitting by common separators
                sections = content.split("\n\n\n")
                if len(sections) > 1:
                    for i, section in enumerate(sections):
                        if section.strip():
                            pages.append(
                                ParsedPage(
                                    page_number=i + 1,
                                    content=section.strip(),
                                    metadata={"extraction_method": "section_split"},
                                )
                            )

            if not pages:
                # Fallback: single page with all content
                pages.append(
                    ParsedPage(
                        page_number=1,
                        content=content.strip(),
                        metadata={"extraction_method": "full_document"},
                    )
                )

        return pages

    def _get_document_type(self, extension: str) -> DocumentType:
        """Get DocumentType from file extension.

        Args:
            extension: File extension (e.g., ".pdf").

        Returns:
            Corresponding DocumentType.
        """
        ext_map = {
            ".pdf": DocumentType.PDF,
            ".jpg": DocumentType.PDF,  # Images treated as single-page PDFs
            ".jpeg": DocumentType.PDF,
            ".png": DocumentType.PDF,
            ".webp": DocumentType.PDF,
        }
        return ext_map.get(extension.lower(), DocumentType.UNKNOWN)

    async def parse_bytes(self, document_bytes: bytes, filename: str = "document.pdf") -> ParseResult:
        """Parse document from bytes directly (without file path).

        This is useful when the document is already in memory.

        Args:
            document_bytes: Document content as bytes.
            filename: Original filename for extension detection.

        Returns:
            ParseResult containing parsed pages and metadata.

        Raises:
            DocumentParsingError: If parsing fails.
        """
        logger.info(f"Parsing document bytes with Modal OCR: {len(document_bytes)} bytes")

        try:
            # Call Modal function
            result = await self._call_modal(document_bytes)

            # Check for errors
            if result.get("error"):
                raise DocumentParsingError(f"Modal OCR failed: {result['error']}")

            # Convert result to ParseResult
            path = Path(filename)
            parse_result = self._convert_to_parse_result(result, path)

            logger.info(
                f"Modal OCR complete: {parse_result.page_count} pages, "
                f"mode={result.get('processing_mode', 'unknown')}"
            )

            return parse_result

        except DocumentParsingError:
            raise
        except Exception as e:
            logger.error(f"Modal OCR failed: {e}", exc_info=True)
            raise DocumentParsingError(
                f"Failed to parse document with Modal: {e}",
                cause=e,
            )


# Convenience function for quick access
async def parse_with_modal(
    file_path: str,
    output_format: str = "markdown",
    force_ocr: bool = False,
) -> ParseResult:
    """Convenience function to parse a document with Modal OCR.

    Args:
        file_path: Path to the document file.
        output_format: Output format ("markdown", "html", or "json").
        force_ocr: Force OCR even for text PDFs.

    Returns:
        ParseResult containing parsed pages and metadata.
    """
    parser = ModalParser(output_format=output_format, force_ocr=force_ocr)
    return await parser.parse(file_path)

