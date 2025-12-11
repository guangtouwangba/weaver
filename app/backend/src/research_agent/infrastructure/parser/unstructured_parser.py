"""Unstructured-based document parser implementation.

This parser uses the Unstructured library to process PDF, Word, and PowerPoint files.
It's a lightweight alternative to Docling that doesn't require PyTorch.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional

from research_agent.infrastructure.parser.base import (
    DocumentParser,
    DocumentParsingError,
    DocumentType,
    ParsedPage,
    ParseResult,
)
from research_agent.shared.utils.logger import logger


class UnstructuredParser(DocumentParser):
    """
    Unstructured-based document parser supporting PDF, DOCX, and PPTX files.

    This is a lightweight parser that doesn't require PyTorch or other heavy
    ML dependencies. Good for fast document processing.

    Features:
    - Fast PDF text extraction
    - Word and PowerPoint support
    - Table extraction (basic)
    - No PyTorch dependency
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

    def __init__(self):
        """Initialize the Unstructured parser."""
        self._partition_func = None

    def _get_partition_func(self, file_extension: str):
        """Get the appropriate partition function for the file type."""
        try:
            if file_extension in [".pdf"]:
                from unstructured.partition.pdf import partition_pdf
                return partition_pdf
            elif file_extension in [".docx", ".doc"]:
                from unstructured.partition.docx import partition_docx
                return partition_docx
            elif file_extension in [".pptx", ".ppt"]:
                from unstructured.partition.pptx import partition_pptx
                return partition_pptx
            else:
                # Generic partition for unknown types
                from unstructured.partition.auto import partition
                return partition
        except ImportError as e:
            raise DocumentParsingError(
                "Unstructured library not installed. Please install it with: "
                "pip install 'unstructured[pdf]'",
                cause=e,
            )

    def supported_formats(self) -> List[str]:
        """Return list of supported MIME types."""
        return self.SUPPORTED_MIME_TYPES.copy()

    def supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()

    async def parse(self, file_path: str) -> ParseResult:
        """
        Parse a document file using Unstructured.

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

        file_extension = path.suffix.lower()
        logger.info(f"Parsing document with Unstructured: {file_path}")

        try:
            # Get appropriate partition function
            partition_func = self._get_partition_func(file_extension)

            # Run partition in thread to not block async loop
            elements = await asyncio.to_thread(
                partition_func,
                filename=str(path),
            )

            # Group elements by page
            pages_dict: Dict[int, List[str]] = {}
            for element in elements:
                # Get page number from metadata (default to 1)
                page_num = 1
                if hasattr(element, "metadata") and element.metadata:
                    page_num = getattr(element.metadata, "page_number", 1) or 1

                if page_num not in pages_dict:
                    pages_dict[page_num] = []

                # Get element text
                text = str(element) if element else ""
                if text.strip():
                    pages_dict[page_num].append(text)

            # Build ParsedPage list
            pages = []
            page_numbers = sorted(pages_dict.keys()) if pages_dict else [1]

            for page_num in page_numbers:
                content_parts = pages_dict.get(page_num, [])
                content = "\n\n".join(content_parts)

                pages.append(
                    ParsedPage(
                        page_number=page_num,
                        content=content,
                        has_ocr=False,  # Unstructured basic mode doesn't do OCR
                        metadata={
                            "extraction_method": "unstructured",
                            "element_count": len(content_parts),
                        },
                    )
                )

            # Determine document type
            doc_type = self.MIME_TO_DOCTYPE.get(
                self._get_mime_type(file_extension),
                DocumentType.PDF,
            )

            logger.info(
                f"Unstructured parsing complete: {len(pages)} pages, "
                f"{sum(len(p.content) for p in pages)} chars total"
            )

            return ParseResult(
                pages=pages,
                document_type=doc_type,
                metadata={
                    "source_file": path.name,
                    "parser": "unstructured",
                    "total_elements": len(elements),
                },
                page_count=len(pages),
                has_ocr=False,
                parser_name=self.parser_name,
            )

        except DocumentParsingError:
            raise
        except Exception as e:
            logger.error(f"Unstructured parsing failed for {file_path}: {e}", exc_info=True)
            raise DocumentParsingError(
                f"Failed to parse document with Unstructured: {e}",
                file_path=file_path,
                cause=e,
            )

    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type from extension."""
        ext_to_mime = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".doc": "application/msword",
            ".ppt": "application/vnd.ms-powerpoint",
        }
        return ext_to_mime.get(extension.lower(), "application/octet-stream")
