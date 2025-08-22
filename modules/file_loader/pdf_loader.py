"""
PDF File Loader

Complete implementation for loading PDF files using pymupdf (fitz).
Supports text extraction, metadata extraction, and error handling.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from .factory import register_file_loader

# PDF处理库
try:
    import fitz  # pymupdf

    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    fitz = None

try:
    import PyPDF2

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    PyPDF2 = None

from ..models import Document, create_document_from_path
from ..schemas.enums import ContentType
from .base import FileLoaderError, IFileLoader

logger = logging.getLogger(__name__)


@register_file_loader(content_type=ContentType.PDF)
class PDFFileLoader(IFileLoader):
    """PDF file loader implementation."""

    def __init__(self, max_file_size: int = 100 * 1024 * 1024):
        """
        Initialize PDF file loader

        Args:
            max_file_size: Maximum file size (bytes), default 100MB
        """
        self.max_file_size = max_file_size
        self._supported_formats = [".pdf"]

        # Check available PDF processing libraries
        if not HAS_PYMUPDF and not HAS_PYPDF2:
            logger.warning(
                "No PDF processing library installed. Recommended installation: pip install pymupdf or pip install PyPDF2"
            )
        elif HAS_PYMUPDF:
            logger.info("PDFFileLoader uses pymupdf (fitz) for PDF processing")
        elif HAS_PYPDF2:
            logger.info("PDFFileLoader uses PyPDF2 for PDF processing")

    @property
    def loader_name(self) -> str:
        """Get loader name"""
        return "PDFFileLoader"

    def supported_formats(self) -> List[str]:
        """Get supported PDF formats"""
        return self._supported_formats.copy()

    def supports_content_type(self, content_type: ContentType) -> bool:
        """Check if specified content type is supported"""
        return content_type == ContentType.PDF

    async def validate_file(self, file_path: str) -> bool:
        """Validate if PDF file can be loaded"""
        try:
            path = Path(file_path)

            # 检查文件是否存在
            if not path.exists():
                logger.error(f"PDF file does not exist: {file_path}")
                return False

            # 检查文件大小
            if path.stat().st_size > self.max_file_size:
                logger.error(
                    f"PDF file too large: {path.stat().st_size} bytes > {self.max_file_size} bytes"
                )
                return False

            # 检查文件扩展名
            if path.suffix.lower() not in self._supported_formats:
                logger.error(f"Unsupported file format: {path.suffix}")
                return False

            # Try to open PDF file to validate format
            if HAS_PYMUPDF:
                try:
                    doc = fitz.open(file_path)
                    page_count = len(doc)
                    doc.close()
                    logger.debug(
                        f"PDF validation successful: {file_path} ({page_count} pages)"
                    )
                    return True
                except Exception as e:
                    logger.error(f"PDF format validation failed (pymupdf): {e}")
                    return False
            elif HAS_PYPDF2:
                try:
                    with open(file_path, "rb") as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        page_count = len(pdf_reader.pages)
                        logger.debug(
                            f"PDF validation successful: {file_path} ({page_count} pages)"
                        )
                        return True
                except Exception as e:
                    logger.error(f"PDF format validation failed (PyPDF2): {e}")
                    return False
            else:
                logger.warning(
                    "No available PDF processing library, skip PDF format validation"
                )
                return True

        except Exception as e:
            logger.error(f"PDF file validation failed: {e}")
            return False

    async def load_document(self, request) -> Document:
        """Load PDF document"""
        from ..models import FileLoadRequest

        # Handle different types of input parameters
        if isinstance(request, str):
            file_path = request
            metadata = {}
        elif isinstance(request, FileLoadRequest):
            file_path = request.file_path
            metadata = request.metadata or {}
        else:
            file_path = request
            metadata = {}

        # Validate file
        if not await self.validate_file(file_path):
            raise FileLoaderError(f"PDF file validation failed: {file_path}")

        try:
            path = Path(file_path)

            # Extract PDF content
            content = await self._extract_pdf_content(path)

            # Extract PDF metadata
            pdf_metadata = await self._extract_pdf_metadata(path)

            # Create document object
            document = create_document_from_path(file_path, content)

            # Update metadata
            document.metadata.update(
                {
                    "loader": self.loader_name,
                    "file_size": path.stat().st_size,
                    "extraction_method": (
                        "pymupdf"
                        if HAS_PYMUPDF
                        else ("PyPDF2" if HAS_PYPDF2 else "placeholder")
                    ),
                    **pdf_metadata,
                    **(metadata or {}),
                }
            )

            logger.info(
                f"Successfully loaded PDF document: {file_path} (page count: {pdf_metadata.get('pdf_pages', 'unknown')}, character count: {len(content)})"
            )
            return document

        except FileLoaderError:
            raise
        except Exception as e:
            logger.error(f"Failed to load PDF document {file_path}: {e}")
            raise FileLoaderError(f"Failed to load PDF document: {str(e)}")

    async def load_documents_batch(self, requests: List) -> List[Document]:
        """Batch load PDF documents"""
        documents = []

        for request in requests:
            try:
                document = await self.load_document(request)
                documents.append(document)

            except FileLoaderError as e:
                logger.error(f"Batch load PDF failed: {e}")
                # Continue processing other documents, do not interrupt entire batch
                continue

        logger.info(
            f"PDF batch loading completed: {len(documents)}/{len(requests)} successful"
        )
        return documents

    async def _extract_pdf_content(self, path: Path) -> str:
        """
        Extract text content from PDF file

        Prioritize pymupdf (fitz), fallback to PyPDF2
        """
        if HAS_PYMUPDF:
            return await self._extract_content_with_pymupdf(path)
        elif HAS_PYPDF2:
            return await self._extract_content_with_pypdf2(path)
        else:
            logger.warning(
                "No PDF processing library installed, return placeholder content"
            )
            return f"[PDF content placeholder: {path.name}]\n\nThis PDF file requires PDF processing library to extract content. Please install: pip install pymupdf or pip install PyPDF2"

    async def _extract_content_with_pymupdf(self, path: Path) -> str:
        """Extract PDF content using pymupdf (fitz)"""
        try:
            # Run CPU-intensive task in async function
            def extract_text():
                doc = fitz.open(str(path))
                text_parts = []

                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    if text.strip():  # Only add non-empty pages
                        text_parts.append(f"--- Page {page_num + 1} pages ---\n{text}")

                doc.close()
                return "\n\n".join(text_parts)

            # Use thread pool executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, extract_text)

            if not content.strip():
                logger.warning(
                    f"PDF file appears to have no extractable text content: {path}"
                )
                return f"[PDF file {path.name} has no extractable text content]"

            return content

        except Exception as e:
            logger.error(f"Failed to extract PDF content using pymupdf: {e}")
            raise FileLoaderError(f"PDF content extraction failed: {e}")

    async def _extract_content_with_pypdf2(self, path: Path) -> str:
        """Extract PDF content using PyPDF2"""
        try:

            def extract_text():
                text_parts = []
                with open(path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)

                    for page_num, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        if text.strip():  # Only add non-empty pages
                            text_parts.append(
                                f"--- Page {page_num + 1} pages ---\n{text}"
                            )

                return "\n\n".join(text_parts)

            # Use thread pool executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, extract_text)

            if not content.strip():
                logger.warning(
                    f"PDF file appears to have no extractable text content: {path}"
                )
                return f"[PDF file {path.name} has no extractable text content]"

            return content

        except Exception as e:
            logger.error(f"Failed to extract PDF content using PyPDF2: {e}")
            raise FileLoaderError(f"PDF content extraction failed: {e}")

    async def _extract_pdf_metadata(self, path: Path) -> Dict[str, Any]:
        """
        Extract PDF metadata

        Prioritize pymupdf (fitz), fallback to PyPDF2
        """
        if HAS_PYMUPDF:
            return await self._extract_metadata_with_pymupdf(path)
        elif HAS_PYPDF2:
            return await self._extract_metadata_with_pypdf2(path)
        else:
            # Basic metadata
            return {
                "pdf_pages": "unknown",
                "pdf_author": "unknown",
                "pdf_title": path.stem,
                "pdf_subject": "unknown",
                "pdf_creator": "unknown",
                "pdf_producer": "unknown",
                "extraction_method": "no_library",
            }

    async def _extract_metadata_with_pymupdf(self, path: Path) -> Dict[str, Any]:
        """Extract PDF metadata using pymupdf (fitz)"""
        try:

            def extract_metadata():
                doc = fitz.open(str(path))
                metadata = doc.metadata
                page_count = len(doc)
                doc.close()

                return {
                    "pdf_pages": page_count,
                    "pdf_title": metadata.get("title", path.stem),
                    "pdf_author": metadata.get("author", "unknown"),
                    "pdf_subject": metadata.get("subject", "unknown"),
                    "pdf_creator": metadata.get("creator", "unknown"),
                    "pdf_producer": metadata.get("producer", "unknown"),
                    "pdf_creation_date": metadata.get("creationDate", "unknown"),
                    "pdf_modification_date": metadata.get("modDate", "unknown"),
                    "extraction_method": "pymupdf",
                }

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, extract_metadata)

        except Exception as e:
            logger.error(f"Failed to extract PDF metadata using pymupdf: {e}")
            return {
                "pdf_pages": "error",
                "pdf_author": "error",
                "pdf_title": path.stem,
                "extraction_method": "pymupdf_error",
                "error": str(e),
            }

    async def _extract_metadata_with_pypdf2(self, path: Path) -> Dict[str, Any]:
        """Extract PDF metadata using PyPDF2"""
        try:

            def extract_metadata():
                with open(path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    metadata = pdf_reader.metadata
                    page_count = len(pdf_reader.pages)

                    return {
                        "pdf_pages": page_count,
                        "pdf_title": (
                            str(metadata.get("/Title", path.stem))
                            if metadata
                            else path.stem
                        ),
                        "pdf_author": (
                            str(metadata.get("/Author", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "pdf_subject": (
                            str(metadata.get("/Subject", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "pdf_creator": (
                            str(metadata.get("/Creator", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "pdf_producer": (
                            str(metadata.get("/Producer", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "pdf_creation_date": (
                            str(metadata.get("/CreationDate", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "pdf_modification_date": (
                            str(metadata.get("/ModDate", "unknown"))
                            if metadata
                            else "unknown"
                        ),
                        "extraction_method": "PyPDF2",
                    }

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, extract_metadata)

        except Exception as e:
            logger.error(f"Failed to extract PDF metadata using PyPDF2: {e}")
        return {
            "pdf_pages": "error",
            "pdf_author": "error",
            "pdf_title": path.stem,
            "extraction_method": "PyPDF2_error",
            "error": str(e),
        }
