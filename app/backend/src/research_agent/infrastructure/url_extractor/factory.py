"""Factory for creating URL extractors."""


from research_agent.infrastructure.url_extractor.base import ExtractionResult, URLExtractor
from research_agent.infrastructure.url_extractor.handlers.bilibili import BilibiliExtractor
from research_agent.infrastructure.url_extractor.handlers.douyin import DouyinExtractor
from research_agent.infrastructure.url_extractor.handlers.webpage import WebPageExtractor
from research_agent.infrastructure.url_extractor.handlers.youtube import YouTubeExtractor
from research_agent.infrastructure.url_extractor.utils import detect_platform, validate_url
from research_agent.shared.utils.logger import logger


class URLExtractorFactory:
    """Factory for creating and using URL extractors."""

    _extractors: list[URLExtractor] = []
    _initialized: bool = False

    @classmethod
    def _initialize(cls) -> None:
        """Initialize the list of available extractors."""
        if not cls._initialized:
            # Order matters: specific extractors first, generic fallback last
            cls._extractors = [
                YouTubeExtractor(),
                BilibiliExtractor(),
                DouyinExtractor(),
                WebPageExtractor(),  # Fallback for any HTTP/HTTPS URL
            ]
            cls._initialized = True

    @classmethod
    def get_extractor(cls, url: str) -> URLExtractor | None:
        """
        Get the appropriate extractor for a URL.

        Args:
            url: The URL to extract content from.

        Returns:
            An extractor that can handle the URL, or None if none found.
        """
        cls._initialize()

        for extractor in cls._extractors:
            if extractor.can_handle(url):
                logger.debug(f"[URLExtractorFactory] Using {extractor.platform} extractor for {url}")
                return extractor

        return None

    @classmethod
    async def extract(cls, url: str) -> ExtractionResult:
        """
        Extract content from a URL using the appropriate extractor.

        Args:
            url: The URL to extract content from.

        Returns:
            ExtractionResult with extracted content or error.
        """
        # Validate URL first
        is_valid, error = validate_url(url)
        if not is_valid:
            return ExtractionResult.failure(error=error or "Invalid URL")

        # Get appropriate extractor
        extractor = cls.get_extractor(url)
        if not extractor:
            return ExtractionResult.failure(
                error="No extractor available for this URL type"
            )

        # Extract content
        platform, video_id = detect_platform(url)
        logger.info(f"[URLExtractorFactory] Extracting URL: {url} (platform={platform})")

        try:
            result = await extractor.extract(url)
            return result
        except Exception as e:
            logger.error(f"[URLExtractorFactory] Extraction failed: {e}", exc_info=True)
            return ExtractionResult.failure(error=str(e))

    @classmethod
    def get_platform(cls, url: str) -> str:
        """
        Get the detected platform for a URL without extracting content.

        Args:
            url: The URL to check.

        Returns:
            Platform identifier (youtube, bilibili, douyin, web).
        """
        platform, _ = detect_platform(url)
        return platform

