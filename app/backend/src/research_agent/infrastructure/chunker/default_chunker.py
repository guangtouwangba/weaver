"""Default chunker using existing ChunkingService strategies.

This chunker wraps the existing ChunkingService to provide a
registry-compatible interface while preserving all current functionality.
"""

from typing import Any

from research_agent.domain.services.chunking_service import (
    ChunkConfig as LegacyChunkConfig,
)
from research_agent.domain.services.chunking_service import (
    ChunkingService,
)
from research_agent.infrastructure.chunker.base import (
    ChunkConfig,
    Chunker,
    ChunkResult,
    PageLike,
)


class DefaultChunker(Chunker):
    """
    Default chunker that wraps the existing ChunkingService.

    This is a catch-all chunker that handles any format not handled
    by a more specific chunker. It uses the existing dynamic strategy
    selection from ChunkingService.
    """

    def supported_mime_types(self) -> list[str]:
        # Supports all types as fallback
        return ["*/*"]

    def supported_extensions(self) -> list[str]:
        # Supports all extensions as fallback
        return [".*"]

    def can_chunk(
        self,
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> bool:
        # Always returns True as this is the catch-all chunker
        return True

    def _get_legacy_config(self) -> LegacyChunkConfig:
        """Convert ChunkConfig to legacy ChunkConfig."""
        return LegacyChunkConfig(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            min_chunk_size=self.config.min_chunk_size,
        )

    def chunk_pages(
        self,
        pages: list[PageLike],
    ) -> ChunkResult:
        """Chunk pages using ChunkingService."""
        service = ChunkingService(self._get_legacy_config())

        # Get mime_type and filename from config.extra if available
        mime_type = self.config.extra.get("mime_type", "application/pdf")
        filename = self.config.extra.get("filename", "document.pdf")

        chunks = service.chunk_pages(pages, mime_type=mime_type, filename=filename)

        return ChunkResult(
            chunks=chunks,
            chunker_name=self.chunker_name,
            strategy_used="ChunkingService (dynamic)",
        )

    def chunk_text(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ChunkResult:
        """Chunk text using ChunkingService."""
        service = ChunkingService(self._get_legacy_config())

        # Get mime_type and filename from config.extra if available
        mime_type = self.config.extra.get("mime_type", "text/plain")
        filename = self.config.extra.get("filename", "document.txt")

        chunks = service.chunk_text(
            text,
            mime_type=mime_type,
            filename=filename,
            metadata=metadata,
        )

        return ChunkResult(
            chunks=chunks,
            chunker_name=self.chunker_name,
            strategy_used="ChunkingService (dynamic)",
        )
