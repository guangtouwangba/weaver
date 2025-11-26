"""PyMuPDF PDF parser implementation."""

import asyncio
from typing import List

import fitz  # PyMuPDF

from research_agent.infrastructure.pdf.base import PDFPage, PDFParser
from research_agent.shared.exceptions import PDFProcessingError


class PyMuPDFParser(PDFParser):
    """PyMuPDF-based PDF parser."""

    async def extract_text(self, file_path: str) -> List[PDFPage]:
        """Extract text from PDF file."""
        try:
            # Run in thread pool to avoid blocking
            return await asyncio.to_thread(self._extract_text_sync, file_path)
        except Exception as e:
            raise PDFProcessingError(f"Failed to extract text from PDF: {e}")

    def _extract_text_sync(self, file_path: str) -> List[PDFPage]:
        """Synchronous text extraction."""
        pages = []
        doc = fitz.open(file_path)

        try:
            for page_num, page in enumerate(doc):
                text = page.get_text()
                pages.append(
                    PDFPage(
                        page_number=page_num + 1,
                        content=text.strip(),
                    )
                )
        finally:
            doc.close()

        return pages

    async def get_page_count(self, file_path: str) -> int:
        """Get number of pages in PDF."""
        try:
            return await asyncio.to_thread(self._get_page_count_sync, file_path)
        except Exception as e:
            raise PDFProcessingError(f"Failed to get page count: {e}")

    def _get_page_count_sync(self, file_path: str) -> int:
        """Synchronous page count."""
        doc = fitz.open(file_path)
        try:
            return len(doc)
        finally:
            doc.close()

