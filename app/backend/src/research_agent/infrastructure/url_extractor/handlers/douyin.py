"""Douyin video content extractor."""

import re
from typing import Optional

from research_agent.infrastructure.url_extractor.base import ExtractionResult, URLExtractor
from research_agent.infrastructure.url_extractor.utils import PLATFORM_PATTERNS
from research_agent.shared.utils.logger import logger


class DouyinExtractor(URLExtractor):
    """
    Extractor for Douyin videos.

    Note: Douyin has aggressive anti-scraping measures.
    This extractor provides best-effort metadata extraction.
    Transcripts are generally NOT available for Douyin videos.
    """

    @property
    def platform(self) -> str:
        return "douyin"

    def can_handle(self, url: str) -> bool:
        """Check if URL is a Douyin video."""
        for pattern in PLATFORM_PATTERNS.get("douyin", []):
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from Douyin URL."""
        for pattern in PLATFORM_PATTERNS.get("douyin", []):
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    async def extract(self, url: str) -> ExtractionResult:
        """Extract content from Douyin video."""
        video_id = self._extract_video_id(url)
        if not video_id:
            return ExtractionResult.failure(
                error="Could not extract video ID from URL",
                title=url,
            )

        logger.info(f"[DouyinExtractor] Extracting video: {video_id}")

        try:
            # Resolve short URL if needed
            resolved_url = await self._resolve_short_url(url) if "v.douyin.com" in url else url

            # Try to scrape video page
            metadata = await self._scrape_video_page(resolved_url, video_id)

            title = metadata.get("title", f"Douyin Video ({video_id})")
            description = metadata.get("description", "")
            thumbnail_url = metadata.get("thumbnail_url")
            creator = metadata.get("creator")

            # Use description as content (no transcripts for Douyin)
            content = description

            result = ExtractionResult(
                success=True,
                title=title,
                content=content,
                thumbnail_url=thumbnail_url,
                platform="douyin",
                content_type="video",
                metadata={
                    "video_id": video_id,
                    "channel_name": creator,
                    "has_transcript": False,  # Douyin never has transcripts
                    "resolved_url": resolved_url if resolved_url != url else None,
                },
            )

            logger.info(
                f"[DouyinExtractor] Extracted: title='{title}', "
                f"content_length={len(content) if content else 0}"
            )

            return result

        except Exception as e:
            logger.error(f"[DouyinExtractor] Error extracting {video_id}: {e}", exc_info=True)
            return ExtractionResult.failure(
                error=str(e),
                title=f"Douyin Video ({video_id})",
            )

    async def _resolve_short_url(self, url: str) -> str:
        """Resolve v.douyin.com short URL to full URL."""
        import httpx

        try:
            async with httpx.AsyncClient(
                timeout=10,
                follow_redirects=False,
                headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
                },
            ) as client:
                response = await client.get(url)

                # Follow redirect chain
                if response.status_code in (301, 302, 303, 307, 308):
                    return response.headers.get("location", url)

        except Exception as e:
            logger.warning(f"[DouyinExtractor] Failed to resolve short URL: {e}")

        return url

    async def _scrape_video_page(self, url: str, video_id: str) -> dict:
        """
        Scrape video page for metadata.

        Note: This may fail due to Douyin's anti-bot measures.
        """
        import httpx

        try:
            async with httpx.AsyncClient(
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                },
                follow_redirects=True,
            ) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    html = response.text

                    # Try to extract title from page
                    title = self._extract_from_html(
                        html,
                        [
                            r'<title[^>]*>(.*?)(?:\s*-\s*抖音|</title>)',
                            r'"desc"\s*:\s*"([^"]+)"',
                            r'"title"\s*:\s*"([^"]+)"',
                        ],
                    )

                    # Try to extract description
                    description = self._extract_from_html(
                        html,
                        [
                            r'"desc"\s*:\s*"([^"]+)"',
                            r'"share_desc"\s*:\s*"([^"]+)"',
                        ],
                    )

                    # Try to extract thumbnail
                    thumbnail_url = self._extract_from_html(
                        html,
                        [
                            r'"cover"\s*:\s*\{\s*"url_list"\s*:\s*\["([^"]+)"',
                            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
                        ],
                    )

                    # Try to extract creator
                    creator = self._extract_from_html(
                        html,
                        [
                            r'"nickname"\s*:\s*"([^"]+)"',
                            r'"author"\s*:\s*\{[^}]*"nickname"\s*:\s*"([^"]+)"',
                        ],
                    )

                    return {
                        "title": title,
                        "description": description,
                        "thumbnail_url": thumbnail_url,
                        "creator": creator,
                    }

        except Exception as e:
            logger.warning(f"[DouyinExtractor] Scrape failed for {video_id}: {e}")

        return {}

    def _extract_from_html(self, html: str, patterns: list[str]) -> Optional[str]:
        """Try multiple regex patterns to extract content from HTML."""
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                text = match.group(1).strip()
                # Decode unicode escapes
                try:
                    text = text.encode().decode("unicode_escape")
                except Exception:
                    pass
                return text
        return None

