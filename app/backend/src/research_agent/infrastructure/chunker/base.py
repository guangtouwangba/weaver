"""Chunker abstract interface.

This module defines the base interface for all chunkers,
supporting multiple document formats with format-specific chunking logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PageLike(Protocol):
    """Protocol for page-like objects (PDFPage, ParsedPage, etc.)."""

    page_number: int
    content: str


@dataclass
class ChunkResult:
    """Result of chunking operation."""

    chunks: list[dict[str, Any]]
    chunker_name: str
    strategy_used: str | None = None


@dataclass
class ChunkConfig:
    """Chunking configuration."""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    extra: dict[str, Any] = field(default_factory=dict)


class Chunker(ABC):
    """
    Abstract chunker interface.

    All format-specific chunkers should inherit from this class and implement
    the required methods. This enables a pluggable architecture where new
    format support can be added without modifying core processing logic.
    """

    def __init__(self, config: ChunkConfig | None = None):
        self.config = config or ChunkConfig()

    @property
    def chunker_name(self) -> str:
        """Return the name of this chunker."""
        return self.__class__.__name__

    @abstractmethod
    def supported_mime_types(self) -> list[str]:
        """
        Return list of MIME types this chunker supports.

        Returns:
            List of MIME type strings (e.g., ["text/csv"])
        """
        pass

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """
        Return list of file extensions this chunker supports.

        Returns:
            List of extension strings with dot prefix (e.g., [".csv"])
        """
        pass

    @abstractmethod
    def chunk_pages(
        self,
        pages: list[PageLike],
    ) -> ChunkResult:
        """
        Chunk pages into smaller pieces.

        Args:
            pages: List of page-like objects with page_number and content.

        Returns:
            ChunkResult with list of chunk dictionaries.
        """
        pass

    @abstractmethod
    def chunk_text(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ChunkResult:
        """
        Chunk raw text into smaller pieces.

        Args:
            text: Text content to chunk.
            metadata: Optional metadata to include with chunks.

        Returns:
            ChunkResult with list of chunk dictionaries.
        """
        pass

    def can_chunk(
        self,
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> bool:
        """
        Check if this chunker supports the given format.

        Args:
            mime_type: MIME type string (e.g., "text/csv").
            extension: File extension (e.g., ".csv" or "csv").

        Returns:
            True if this chunker can handle the format.
        """
        if mime_type and mime_type in self.supported_mime_types():
            return True

        if extension:
            ext = extension.lower()
            if not ext.startswith("."):
                ext = f".{ext}"
            return ext in self.supported_extensions()

        return False
