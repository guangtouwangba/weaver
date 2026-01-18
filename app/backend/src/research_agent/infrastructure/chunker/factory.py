"""Chunker factory and registry.

This module provides the ChunkerRegistry and ChunkerFactory for
managing chunkers across different file formats.
"""

from typing import Any

from research_agent.infrastructure.chunker.base import (
    ChunkConfig,
    Chunker,
    ChunkResult,
    PageLike,
)
from research_agent.shared.utils.logger import logger


class ChunkerRegistry:
    """
    Registry for chunkers.

    Maintains a list of registered chunkers and provides lookup
    by MIME type or file extension.
    """

    def __init__(self):
        self._chunkers: list[Chunker] = []

    def register(self, chunker: Chunker) -> None:
        """
        Register a chunker.

        Args:
            chunker: Chunker instance to register.
        """
        self._chunkers.append(chunker)
        logger.debug(
            f"Registered chunker {chunker.chunker_name} "
            f"for MIME: {chunker.supported_mime_types()}, "
            f"extensions: {chunker.supported_extensions()}"
        )

    def get_chunker(
        self,
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> Chunker | None:
        """
        Get a chunker for the given format.

        Args:
            mime_type: MIME type string.
            extension: File extension.

        Returns:
            Matching Chunker or None if not found.
        """
        for chunker in self._chunkers:
            if chunker.can_chunk(mime_type, extension):
                return chunker
        return None

    def is_supported(
        self,
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> bool:
        """
        Check if a registered chunker exists for the given format.

        Args:
            mime_type: MIME type string.
            extension: File extension.

        Returns:
            True if a chunker exists for the format.
        """
        return self.get_chunker(mime_type, extension) is not None


# Module-level registry instance
_registry = ChunkerRegistry()
_initialized = False


def _initialize_default_chunkers() -> None:
    """Initialize and register default chunkers."""
    global _initialized
    if _initialized:
        return

    from research_agent.infrastructure.chunker.csv_chunker import (
        CSVChunker,
    )
    from research_agent.infrastructure.chunker.default_chunker import (
        DefaultChunker,
    )
    from research_agent.infrastructure.chunker.transcript_chunker import (
        TranscriptChunker,
    )

    _registry.register(CSVChunker())
    _registry.register(TranscriptChunker())
    _registry.register(DefaultChunker())  # Register last as catch-all

    _initialized = True
    logger.info("Default chunkers registered (CSV, Transcript, Default)")


class ChunkerFactory:
    """
    Factory for chunking operations.

    Provides static methods for checking format support and chunking
    content using the appropriate registered chunker.
    """

    @staticmethod
    def get_chunker(
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> Chunker | None:
        """
        Get a chunker for the given format.

        Args:
            mime_type: MIME type string.
            extension: File extension.

        Returns:
            Chunker or None.
        """
        _initialize_default_chunkers()
        return _registry.get_chunker(mime_type, extension)

    @staticmethod
    def is_supported(
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> bool:
        """
        Check if chunking is supported for the given format.

        Note: With DefaultChunker registered, this will almost always
        return True. Use get_chunker() to get specific chunker if needed.

        Args:
            mime_type: MIME type string.
            extension: File extension.

        Returns:
            True if supported.
        """
        _initialize_default_chunkers()
        return _registry.is_supported(mime_type, extension)

    @staticmethod
    def chunk_pages(
        pages: list[PageLike],
        mime_type: str | None = None,
        extension: str | None = None,
        config: ChunkConfig | None = None,
    ) -> ChunkResult:
        """
        Chunk pages using the appropriate chunker.

        Args:
            pages: List of page-like objects.
            mime_type: MIME type string.
            extension: File extension.
            config: Optional chunk configuration.

        Returns:
            ChunkResult with list of chunks.
        """
        _initialize_default_chunkers()

        chunker = _registry.get_chunker(mime_type, extension)
        if chunker is None:
            # Fallback to default chunker
            from research_agent.infrastructure.chunker.default_chunker import (
                DefaultChunker,
            )

            chunker = DefaultChunker(config)

        if config:
            chunker.config = config

        logger.info(
            f"[ChunkerFactory] Using {chunker.chunker_name} " f"for {extension or mime_type}"
        )
        return chunker.chunk_pages(pages)

    @staticmethod
    def chunk_text(
        text: str,
        mime_type: str | None = None,
        extension: str | None = None,
        metadata: dict[str, Any] | None = None,
        config: ChunkConfig | None = None,
    ) -> ChunkResult:
        """
        Chunk text using the appropriate chunker.

        Args:
            text: Text content to chunk.
            mime_type: MIME type string.
            extension: File extension.
            metadata: Optional metadata.
            config: Optional chunk configuration.

        Returns:
            ChunkResult with list of chunks.
        """
        _initialize_default_chunkers()

        chunker = _registry.get_chunker(mime_type, extension)
        if chunker is None:
            from research_agent.infrastructure.chunker.default_chunker import (
                DefaultChunker,
            )

            chunker = DefaultChunker(config)

        if config:
            chunker.config = config

        logger.info(
            f"[ChunkerFactory] Using {chunker.chunker_name} " f"for {extension or mime_type}"
        )
        return chunker.chunk_text(text, metadata)
