"""Thumbnail generator factory and registry.

This module provides the ThumbnailRegistry and ThumbnailFactory for
managing thumbnail generators across different file formats.
"""

from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from research_agent.infrastructure.thumbnail.base import (
    ThumbnailGenerator,
    ThumbnailResult,
)
from research_agent.shared.utils.logger import logger

if TYPE_CHECKING:
    pass


class ThumbnailRegistry:
    """
    Registry for thumbnail generators.

    Maintains a list of registered generators and provides lookup
    by MIME type or file extension.
    """

    def __init__(self):
        self._generators: list[ThumbnailGenerator] = []

    def register(self, generator: ThumbnailGenerator) -> None:
        """
        Register a thumbnail generator.

        Args:
            generator: Generator instance to register.
        """
        self._generators.append(generator)
        logger.debug(
            f"Registered thumbnail generator {generator.generator_name} "
            f"for MIME: {generator.supported_mime_types()}, "
            f"extensions: {generator.supported_extensions()}"
        )

    def get_generator(
        self,
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> ThumbnailGenerator | None:
        """
        Get a generator for the given format.

        Args:
            mime_type: MIME type string (e.g., "application/pdf").
            extension: File extension (e.g., ".pdf" or "pdf").

        Returns:
            Matching ThumbnailGenerator or None if not found.
        """
        for gen in self._generators:
            if gen.can_generate(mime_type, extension):
                return gen
        return None

    def is_supported(
        self,
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> bool:
        """
        Check if thumbnail generation is supported for the given format.

        Args:
            mime_type: MIME type string.
            extension: File extension.

        Returns:
            True if a generator exists for the format.
        """
        return self.get_generator(mime_type, extension) is not None


# Module-level registry instance
_registry = ThumbnailRegistry()
_initialized = False


def _initialize_default_generators() -> None:
    """Initialize and register default thumbnail generators."""
    global _initialized
    if _initialized:
        return

    from research_agent.infrastructure.thumbnail.pdf_generator import (
        PDFThumbnailGenerator,
    )
    from research_agent.infrastructure.thumbnail.text_generator import (
        TextThumbnailGenerator,
    )

    _registry.register(PDFThumbnailGenerator())
    _registry.register(TextThumbnailGenerator())

    _initialized = True
    logger.info("Default thumbnail generators registered (PDF, Text)")


class ThumbnailFactory:
    """
    Factory for thumbnail generation.

    Provides static methods for checking format support and generating
    thumbnails using the appropriate registered generator.
    """

    @staticmethod
    def get_generator(
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> ThumbnailGenerator | None:
        """
        Get a generator for the given format.

        Args:
            mime_type: MIME type string.
            extension: File extension.

        Returns:
            ThumbnailGenerator or None.
        """
        _initialize_default_generators()
        return _registry.get_generator(mime_type, extension)

    @staticmethod
    def is_supported(
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> bool:
        """
        Check if thumbnail generation is supported for the given format.

        Args:
            mime_type: MIME type string.
            extension: File extension.

        Returns:
            True if supported.
        """
        _initialize_default_generators()
        return _registry.is_supported(mime_type, extension)

    @staticmethod
    async def generate(
        file_path: str,
        document_id: UUID,
        output_dir: Path,
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> ThumbnailResult:
        """
        Generate thumbnail using the appropriate generator.

        Args:
            file_path: Path to source file.
            document_id: Document UUID for output filename.
            output_dir: Directory to save thumbnail.
            mime_type: MIME type string.
            extension: File extension.

        Returns:
            ThumbnailResult with path and success status.
        """
        _initialize_default_generators()

        generator = _registry.get_generator(mime_type, extension)
        if generator is None:
            return ThumbnailResult(
                path=None,
                success=False,
                error=f"No thumbnail generator for mime_type={mime_type}, extension={extension}",
            )

        logger.info(
            f"[ThumbnailFactory] Using {generator.generator_name} " f"for {extension or mime_type}"
        )
        return await generator.generate(file_path, document_id, output_dir)
