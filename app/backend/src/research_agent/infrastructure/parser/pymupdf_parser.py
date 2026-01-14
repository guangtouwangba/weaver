"""PyMuPDF-based document parser implementation.

This parser uses PyMuPDF (fitz) for PDF processing. It's lightweight
and doesn't require system dependencies like libGL.
"""

import asyncio
from pathlib import Path

from research_agent.infrastructure.parser.base import (
    DocumentParser,
    DocumentParsingError,
    DocumentType,
    ParsedPage,
    ParseResult,
)
from research_agent.shared.utils.logger import logger


class PyMuPDFDocumentParser(DocumentParser):
    """
    PyMuPDF-based document parser for PDF files.

    This is a lightweight parser that only requires PyMuPDF (~30MB),
    with no system dependencies (no libGL, no cv2).

    Features:
    - Fast PDF text extraction
    - No system dependencies
    - Small footprint
    """

    SUPPORTED_MIME_TYPES = ["application/pdf"]
    SUPPORTED_EXTENSIONS = [".pdf"]

    def supported_formats(self) -> list[str]:
        """Return list of supported MIME types."""
        return self.SUPPORTED_MIME_TYPES.copy()

    def supported_extensions(self) -> list[str]:
        """Return list of supported file extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()

    async def parse(self, file_path: str) -> ParseResult:
        """
        Parse a PDF file using PyMuPDF.

        Args:
            file_path: Path to the PDF file.

        Returns:
            ParseResult containing pages and metadata.

        Raises:
            DocumentParsingError: If parsing fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentParsingError(f"File not found: {file_path}", file_path=file_path)

        logger.info(f"Parsing PDF with PyMuPDF: {file_path}")

        try:
            # Import fitz lazily
            import fitz

            # Run in thread pool to avoid blocking
            pages = await asyncio.to_thread(self._extract_pages_sync, file_path, fitz)

            logger.info(
                f"PyMuPDF parsing complete: {len(pages)} pages, "
                f"{sum(len(p.content) for p in pages)} chars total"
            )

            return ParseResult(
                pages=pages,
                document_type=DocumentType.PDF,
                metadata={
                    "source_file": path.name,
                    "parser": "pymupdf",
                },
                page_count=len(pages),
                has_ocr=False,
                parser_name=self.parser_name,
            )

        except ImportError as e:
            raise DocumentParsingError(
                "PyMuPDF not installed. Please install it with: pip install pymupdf",
                file_path=file_path,
                cause=e,
            )
        except Exception as e:
            logger.error(f"PyMuPDF parsing failed for {file_path}: {e}", exc_info=True)
            raise DocumentParsingError(
                f"Failed to parse PDF with PyMuPDF: {e}",
                file_path=file_path,
                cause=e,
            )

    def _extract_pages_sync(self, file_path: str, fitz) -> list[ParsedPage]:
        """Synchronous page extraction."""
        pages = []
        doc = fitz.open(file_path)

        try:
            for page_num, page in enumerate(doc):
                text = page.get_text()
                pages.append(
                    ParsedPage(
                        page_number=page_num + 1,
                        content=text.strip(),
                        has_ocr=False,
                        metadata={"extraction_method": "pymupdf"},
                    )
                )
        finally:
            doc.close()

        return pages
