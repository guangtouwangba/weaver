"""PDF parser abstract interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class PDFPage:
    """PDF page data class."""

    page_number: int
    content: str


class PDFParser(ABC):
    """Abstract PDF parser interface."""

    @abstractmethod
    async def extract_text(self, file_path: str) -> List[PDFPage]:
        """Extract text from PDF file."""
        pass

    @abstractmethod
    async def get_page_count(self, file_path: str) -> int:
        """Get number of pages in PDF."""
        pass

