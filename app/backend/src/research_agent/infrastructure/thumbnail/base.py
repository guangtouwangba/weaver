"""Thumbnail generator abstract interface.

This module defines the base interface for all thumbnail generators,
supporting multiple document formats including PDF, text, and images.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID


@dataclass
class ThumbnailResult:
    """Result of thumbnail generation."""

    path: str | None
    success: bool
    error: str | None = None


class ThumbnailGenerator(ABC):
    """
    Abstract thumbnail generator interface.

    All format-specific generators should inherit from this class and implement
    the required methods. This enables a pluggable architecture where new
    format support can be added without modifying core processing logic.
    """

    @property
    def generator_name(self) -> str:
        """Return the name of this generator."""
        return self.__class__.__name__

    @abstractmethod
    def supported_mime_types(self) -> list[str]:
        """
        Return list of MIME types this generator supports.

        Returns:
            List of MIME type strings (e.g., ["application/pdf"])
        """
        pass

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """
        Return list of file extensions this generator supports.

        Returns:
            List of extension strings with dot prefix (e.g., [".pdf"])
        """
        pass

    @abstractmethod
    async def generate(
        self,
        file_path: str,
        document_id: UUID,
        output_dir: Path,
    ) -> ThumbnailResult:
        """
        Generate thumbnail for the given file.

        Args:
            file_path: Path to the source file.
            document_id: Document UUID for output filename.
            output_dir: Directory to save the generated thumbnail.

        Returns:
            ThumbnailResult with path and success status.
        """
        pass

    def can_generate(
        self,
        mime_type: str | None = None,
        extension: str | None = None,
    ) -> bool:
        """
        Check if this generator supports the given format.

        Args:
            mime_type: MIME type string (e.g., "application/pdf").
            extension: File extension (e.g., ".pdf" or "pdf").

        Returns:
            True if this generator can handle the format.
        """
        if mime_type and mime_type in self.supported_mime_types():
            return True

        if extension:
            ext = extension.lower()
            if not ext.startswith("."):
                ext = f".{ext}"
            return ext in self.supported_extensions()

        return False
