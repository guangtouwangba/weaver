"""Text chunking service."""

from dataclasses import dataclass
from typing import List

from research_agent.infrastructure.pdf.base import PDFPage


@dataclass
class ChunkConfig:
    """Chunking configuration."""

    chunk_size: int = 500
    chunk_overlap: int = 50


class ChunkingService:
    """Service for chunking text into smaller pieces."""

    def __init__(self, config: ChunkConfig | None = None):
        self.config = config or ChunkConfig()

    def chunk_pages(self, pages: List[PDFPage]) -> List[dict]:
        """Chunk PDF pages into smaller pieces."""
        chunks = []
        chunk_index = 0

        for page in pages:
            page_chunks = self._chunk_text(page.content, page.page_number)
            for chunk_content in page_chunks:
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": chunk_content,
                        "page_number": page.page_number,
                    }
                )
                chunk_index += 1

        return chunks

    def _chunk_text(self, text: str, page_number: int) -> List[str]:
        """Split text into chunks with overlap."""
        if not text.strip():
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.config.chunk_size

            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence end within the last 100 chars
                search_start = max(start + self.config.chunk_size - 100, start)
                for sep in [".", "!", "?", "\n\n", "\n"]:
                    last_sep = text.rfind(sep, search_start, end)
                    if last_sep > start:
                        end = last_sep + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - self.config.chunk_overlap
            if start >= text_length:
                break

        return chunks

