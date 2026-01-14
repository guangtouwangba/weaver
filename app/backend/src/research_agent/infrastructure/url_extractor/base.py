"""Base classes and data structures for URL extraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractionResult:
    """Result of URL content extraction."""

    # Status
    success: bool
    error: str | None = None

    # Core content
    title: str | None = None
    content: str | None = None  # Article text or transcript
    thumbnail_url: str | None = None

    # Platform info
    platform: str = "web"  # youtube, bilibili, douyin, web
    content_type: str = "link"  # video, article, link

    # Platform-specific metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "error": self.error,
            "title": self.title,
            "content": self.content,
            "thumbnail_url": self.thumbnail_url,
            "platform": self.platform,
            "content_type": self.content_type,
            "metadata": self.metadata,
        }

    @classmethod
    def failure(cls, error: str, title: str | None = None) -> "ExtractionResult":
        """Create a failure result."""
        return cls(
            success=False,
            error=error,
            title=title,
        )


class URLExtractor(ABC):
    """Abstract base class for URL extractors."""

    @property
    @abstractmethod
    def platform(self) -> str:
        """Return the platform identifier."""
        pass

    @abstractmethod
    async def extract(self, url: str) -> ExtractionResult:
        """
        Extract content from a URL.

        Args:
            url: The URL to extract content from.

        Returns:
            ExtractionResult containing the extracted content.
        """
        pass

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Check if this extractor can handle the given URL.

        Args:
            url: The URL to check.

        Returns:
            True if this extractor can handle the URL.
        """
        pass

