"""Thumbnail generation module.

Provides extensible thumbnail generation using the Registry pattern.
"""

from research_agent.infrastructure.thumbnail.base import (
    ThumbnailGenerator,
    ThumbnailResult,
)
from research_agent.infrastructure.thumbnail.factory import (
    ThumbnailFactory,
)

__all__ = [
    "ThumbnailGenerator",
    "ThumbnailResult",
    "ThumbnailFactory",
]
