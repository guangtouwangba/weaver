"""URL Extractor module for extracting content from URLs.

This module provides a unified interface for extracting content from various
URL types including web pages, YouTube videos, Bilibili videos, and Douyin videos.
"""

from research_agent.infrastructure.url_extractor.base import (
    ExtractionResult,
    URLExtractor,
)
from research_agent.infrastructure.url_extractor.factory import URLExtractorFactory
from research_agent.infrastructure.url_extractor.utils import (
    detect_platform,
    normalize_url,
    validate_url,
)

__all__ = [
    "ExtractionResult",
    "URLExtractor",
    "URLExtractorFactory",
    "detect_platform",
    "normalize_url",
    "validate_url",
]

