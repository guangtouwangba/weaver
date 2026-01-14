"""Docling-based document parser implementation.

This parser uses the Docling library to process PDF, Word, and PowerPoint files
with advanced features including OCR support, layout analysis, and table extraction.
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


class DoclingParser(DocumentParser):
    """
    Docling-based document parser supporting PDF, DOCX, and PPTX files.

    Features:
    - OCR support for scanned documents
    - Advanced layout analysis
    - Table extraction
    - Multi-column text handling
    """

    # MIME types this parser supports
    SUPPORTED_MIME_TYPES = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # PPTX
        "application/msword",  # DOC (legacy)
        "application/vnd.ms-powerpoint",  # PPT (legacy)
    ]

    SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".pptx", ".doc", ".ppt"]

    # Map MIME types to DocumentType
    MIME_TO_DOCTYPE = {
        "application/pdf": DocumentType.PDF,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.DOCX,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": DocumentType.PPTX,
        "application/msword": DocumentType.DOCX,
        "application/vnd.ms-powerpoint": DocumentType.PPTX,
    }

    def __init__(self, enable_ocr: bool = True):
        """
        Initialize the Docling parser.

        Args:
            enable_ocr: Whether to enable OCR for scanned documents.
        """
        self.enable_ocr = enable_ocr
        self._converter = None

    def _get_converter(self):
        """Lazy initialization of DocumentConverter."""
        if self._converter is None:
            try:
                from docling.document_converter import DocumentConverter

                self._converter = DocumentConverter()
                logger.info("Docling DocumentConverter initialized successfully")
            except ImportError as e:
                raise DocumentParsingError(
                    "Docling library not installed. Please install it with: pip install docling",
                    cause=e,
                )
        return self._converter

    def supported_formats(self) -> list[str]:
        """Return list of supported MIME types."""
        return self.SUPPORTED_MIME_TYPES.copy()

    def supported_extensions(self) -> list[str]:
        """Return list of supported file extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()

    async def parse(self, file_path: str) -> ParseResult:
        """
        Parse a document file using Docling.

        Args:
            file_path: Path to the document file.

        Returns:
            ParseResult containing pages and metadata.

        Raises:
            DocumentParsingError: If parsing fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentParsingError(f"File not found: {file_path}", file_path=file_path)

        logger.info(f"Parsing document with Docling: {file_path}")

        try:
            # Run Docling conversion in thread pool to avoid blocking
            result = await asyncio.to_thread(self._parse_sync, file_path)
            return result
        except DocumentParsingError:
            raise
        except Exception as e:
            logger.error(f"Docling parsing failed for {file_path}: {e}", exc_info=True)
            raise DocumentParsingError(
                f"Failed to parse document: {e}",
                file_path=file_path,
                cause=e,
            )

    def _parse_sync(self, file_path: str) -> ParseResult:
        """Synchronous parsing implementation."""
        converter = self._get_converter()
        path = Path(file_path)

        # Detect document type from extension
        extension = path.suffix.lower()
        doc_type = self._get_document_type(extension)

        # Convert the document
        logger.debug(f"Starting Docling conversion for: {file_path}")
        conversion_result = converter.convert(file_path)

        # Extract document from result
        doc = conversion_result.document

        # Extract pages based on document structure
        pages = self._extract_pages(doc, doc_type)

        # Build metadata
        has_ocr = self._check_ocr_used(conversion_result)
        metadata = {
            "source_file": str(path.name),
            "file_extension": extension,
            "converter_version": "docling",
        }

        # Try to extract additional metadata from the document
        if hasattr(doc, "meta") and doc.meta:
            metadata["document_meta"] = str(doc.meta)

        logger.info(f"Docling parsing complete: {len(pages)} pages extracted, OCR used: {has_ocr}")

        return ParseResult(
            pages=pages,
            document_type=doc_type,
            metadata=metadata,
            page_count=len(pages),
            has_ocr=has_ocr,
            parser_name=self.parser_name,
        )

    def _extract_pages(self, doc, doc_type: DocumentType) -> list[ParsedPage]:
        """
        Extract pages from Docling document object.

        Args:
            doc: Docling document object.
            doc_type: Type of document being processed.

        Returns:
            List of ParsedPage objects.
        """
        pages = []

        # Try to get content by page if available
        try:
            # Export to markdown for full content extraction
            full_content = doc.export_to_markdown()

            # For PDFs, try to split by page markers or use full content
            if doc_type == DocumentType.PDF:
                pages = self._split_pdf_pages(doc, full_content)
            else:
                # For Word/PPT, treat as single content block or split by sections
                pages = self._split_document_sections(doc, full_content)

        except Exception as e:
            logger.warning(f"Failed to extract pages with structure: {e}")
            # Fallback: create single page with all content
            try:
                full_content = doc.export_to_markdown()
                pages = [
                    ParsedPage(
                        page_number=1,
                        content=full_content,
                        metadata={"extraction_method": "fallback"},
                    )
                ]
            except Exception as fallback_e:
                logger.error(f"Fallback extraction also failed: {fallback_e}")
                raise DocumentParsingError(f"Unable to extract content from document: {fallback_e}")

        return pages

    def _split_pdf_pages(self, doc, full_content: str) -> list[ParsedPage]:
        """
        Split PDF content into pages.

        Args:
            doc: Docling document object.
            full_content: Full markdown content.

        Returns:
            List of ParsedPage objects.
        """
        pages = []

        # Try to get page-level information from document structure
        try:
            # Docling provides page-level information through the document model
            if hasattr(doc, "pages") and doc.pages:
                for i, page_content in enumerate(doc.pages):
                    content = ""
                    if hasattr(page_content, "export_to_markdown"):
                        content = page_content.export_to_markdown()
                    elif hasattr(page_content, "text"):
                        content = page_content.text
                    else:
                        content = str(page_content)

                    pages.append(
                        ParsedPage(
                            page_number=i + 1,
                            content=content.strip(),
                            metadata={"extraction_method": "page_level"},
                        )
                    )
                return pages
        except Exception as e:
            logger.debug(f"Page-level extraction not available: {e}")

        # Fallback: use full content as single page or split by page breaks
        if "---" in full_content or "\n\n\n" in full_content:
            # Try to split by common page separators
            sections = full_content.split("\n\n\n")
            for i, section in enumerate(sections):
                if section.strip():
                    pages.append(
                        ParsedPage(
                            page_number=i + 1,
                            content=section.strip(),
                            metadata={"extraction_method": "section_split"},
                        )
                    )
        else:
            # Single page fallback
            pages.append(
                ParsedPage(
                    page_number=1,
                    content=full_content.strip(),
                    metadata={"extraction_method": "full_document"},
                )
            )

        return pages

    def _split_document_sections(self, doc, full_content: str) -> list[ParsedPage]:
        """
        Split Word/PPT content into sections.

        Args:
            doc: Docling document object.
            full_content: Full markdown content.

        Returns:
            List of ParsedPage objects.
        """
        pages = []

        # Try to split by headers (# or ##)
        import re

        header_pattern = r"^#{1,2}\s+.+$"
        lines = full_content.split("\n")

        current_section = []
        section_count = 0

        for line in lines:
            if re.match(header_pattern, line) and current_section:
                # Save previous section
                section_count += 1
                pages.append(
                    ParsedPage(
                        page_number=section_count,
                        content="\n".join(current_section).strip(),
                        metadata={"extraction_method": "header_split"},
                    )
                )
                current_section = [line]
            else:
                current_section.append(line)

        # Add last section
        if current_section:
            section_count += 1
            pages.append(
                ParsedPage(
                    page_number=section_count,
                    content="\n".join(current_section).strip(),
                    metadata={"extraction_method": "header_split"},
                )
            )

        # If no sections found, return as single page
        if not pages:
            pages.append(
                ParsedPage(
                    page_number=1,
                    content=full_content.strip(),
                    metadata={"extraction_method": "full_document"},
                )
            )

        return pages

    def _check_ocr_used(self, conversion_result) -> bool:
        """
        Check if OCR was used during conversion.

        Args:
            conversion_result: Docling conversion result.

        Returns:
            True if OCR was applied.
        """
        try:
            # Check conversion result metadata for OCR indicators
            if hasattr(conversion_result, "metadata"):
                meta = conversion_result.metadata
                if hasattr(meta, "ocr_used") and meta.ocr_used:
                    return True

            # Check document-level OCR flags
            doc = conversion_result.document
            if hasattr(doc, "meta"):
                meta = doc.meta
                if hasattr(meta, "ocr_applied") and meta.ocr_applied:
                    return True

        except Exception:
            pass

        return False

    def _get_document_type(self, extension: str) -> DocumentType:
        """
        Get DocumentType from file extension.

        Args:
            extension: File extension (e.g., ".pdf").

        Returns:
            Corresponding DocumentType.
        """
        ext_map = {
            ".pdf": DocumentType.PDF,
            ".docx": DocumentType.DOCX,
            ".doc": DocumentType.DOCX,
            ".pptx": DocumentType.PPTX,
            ".ppt": DocumentType.PPTX,
        }
        return ext_map.get(extension.lower(), DocumentType.UNKNOWN)
