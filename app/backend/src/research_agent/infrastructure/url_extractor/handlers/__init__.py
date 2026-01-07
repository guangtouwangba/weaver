"""URL extraction handlers for different platforms."""

from research_agent.infrastructure.url_extractor.handlers.bilibili import (
    BilibiliExtractor,
)
from research_agent.infrastructure.url_extractor.handlers.douyin import DouyinExtractor
from research_agent.infrastructure.url_extractor.handlers.webpage import WebPageExtractor
from research_agent.infrastructure.url_extractor.handlers.youtube import YouTubeExtractor

__all__ = [
    "YouTubeExtractor",
    "BilibiliExtractor",
    "DouyinExtractor",
    "WebPageExtractor",
]

