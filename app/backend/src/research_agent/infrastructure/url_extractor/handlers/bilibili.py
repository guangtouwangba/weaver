"""Bilibili video content extractor."""

import re
from typing import Optional

from research_agent.infrastructure.url_extractor.base import ExtractionResult, URLExtractor
from research_agent.infrastructure.url_extractor.utils import (
    PLATFORM_PATTERNS,
    truncate_content,
)
from research_agent.shared.utils.logger import logger


class BilibiliExtractor(URLExtractor):
    """Extractor for Bilibili videos."""

    @property
    def platform(self) -> str:
        return "bilibili"

    def can_handle(self, url: str) -> bool:
        """Check if URL is a Bilibili video."""
        for pattern in PLATFORM_PATTERNS.get("bilibili", []):
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID (BV number) from Bilibili URL."""
        for pattern in PLATFORM_PATTERNS.get("bilibili", []):
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    async def extract(self, url: str) -> ExtractionResult:
        """Extract content from Bilibili video."""
        video_id = self._extract_video_id(url)
        if not video_id:
            return ExtractionResult.failure(
                error="Could not extract video ID from URL",
                title=url,
            )

        logger.info(f"[BilibiliExtractor] Extracting video: {video_id}")

        try:
            # Try using bilibili-api-python
            metadata = await self._get_video_metadata(video_id)

            if not metadata.get("success"):
                # Fallback to basic scraping
                metadata = await self._scrape_video_page(url, video_id)

            title = metadata.get("title", f"Bilibili Video ({video_id})")
            description = metadata.get("description", "")
            thumbnail_url = metadata.get("thumbnail_url")
            uploader = metadata.get("uploader")
            duration = metadata.get("duration")

            # Try to get subtitles
            subtitle_text, has_transcript = await self._get_subtitles(video_id)

            # Use description as content if no subtitles
            content = subtitle_text if subtitle_text else description
            if content:
                content = truncate_content(content)

            result = ExtractionResult(
                success=True,
                title=title,
                content=content,
                thumbnail_url=thumbnail_url,
                platform="bilibili",
                content_type="video",
                metadata={
                    "video_id": video_id,
                    "channel_name": uploader,
                    "duration": duration,
                    "has_transcript": has_transcript,
                    "view_count": metadata.get("view_count"),
                    "like_count": metadata.get("like_count"),
                },
            )

            logger.info(
                f"[BilibiliExtractor] Extracted: title='{title}', "
                f"content_length={len(content) if content else 0}, "
                f"has_transcript={has_transcript}"
            )

            return result

        except Exception as e:
            logger.error(f"[BilibiliExtractor] Error extracting {video_id}: {e}", exc_info=True)
            return ExtractionResult.failure(
                error=str(e),
                title=f"Bilibili Video ({video_id})",
            )

    async def _get_video_metadata(self, video_id: str) -> dict:
        """Get video metadata using bilibili-api-python."""
        try:
            from bilibili_api import video

            import asyncio

            v = video.Video(bvid=video_id)
            info = await v.get_info()

            return {
                "success": True,
                "title": info.get("title"),
                "description": info.get("desc"),
                "thumbnail_url": info.get("pic"),
                "uploader": info.get("owner", {}).get("name"),
                "duration": info.get("duration"),
                "view_count": info.get("stat", {}).get("view"),
                "like_count": info.get("stat", {}).get("like"),
            }

        except Exception as e:
            logger.warning(f"[BilibiliExtractor] API failed for {video_id}: {e}")
            return {"success": False}

    async def _scrape_video_page(self, url: str, video_id: str) -> dict:
        """Fallback: scrape video page for basic metadata."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    follow_redirects=True,
                )

                if response.status_code == 200:
                    html = response.text

                    # Extract title from page
                    title_match = re.search(
                        r'<title[^>]*>(.*?)_哔哩哔哩', html, re.IGNORECASE | re.DOTALL
                    )
                    title = title_match.group(1).strip() if title_match else None

                    # Extract thumbnail from og:image
                    og_match = re.search(
                        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
                        html,
                        re.IGNORECASE,
                    )
                    thumbnail_url = og_match.group(1) if og_match else None

                    return {
                        "success": True,
                        "title": title,
                        "thumbnail_url": thumbnail_url,
                    }

        except Exception as e:
            logger.warning(f"[BilibiliExtractor] Scrape failed for {video_id}: {e}")

        return {"success": False}

    async def _get_subtitles(self, video_id: str) -> tuple[Optional[str], bool]:
        """
        Try to get subtitles for a Bilibili video.

        Note: Most Bilibili videos don't have subtitles.

        Returns:
            Tuple of (subtitle_text, has_transcript).
        """
        try:
            from bilibili_api import video

            v = video.Video(bvid=video_id)

            # Get player info which contains subtitle URLs
            player_info = await v.get_player_info()

            subtitle_list = player_info.get("subtitle", {}).get("subtitles", [])
            if not subtitle_list:
                logger.info(f"[BilibiliExtractor] No subtitles for {video_id}")
                return None, False

            # Get first subtitle (usually the primary language)
            import httpx

            subtitle_url = subtitle_list[0].get("subtitle_url")
            if not subtitle_url:
                return None, False

            # Ensure URL has protocol
            if subtitle_url.startswith("//"):
                subtitle_url = "https:" + subtitle_url

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(subtitle_url)
                if response.status_code == 200:
                    subtitle_data = response.json()
                    body = subtitle_data.get("body", [])

                    # Join subtitle segments
                    text = " ".join(item.get("content", "") for item in body)
                    return text.strip(), True

        except Exception as e:
            logger.warning(f"[BilibiliExtractor] Subtitle fetch failed for {video_id}: {e}")

        return None, False

