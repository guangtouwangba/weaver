"""Web page content extractor using trafilatura."""

import asyncio
from typing import Optional

from research_agent.infrastructure.url_extractor.base import ExtractionResult, URLExtractor
from research_agent.infrastructure.url_extractor.utils import truncate_content
from research_agent.shared.utils.logger import logger


class WebPageExtractor(URLExtractor):
    """Extractor for generic web pages using trafilatura."""

    @property
    def platform(self) -> str:
        return "web"

    def can_handle(self, url: str) -> bool:
        """Web page extractor handles all HTTP/HTTPS URLs as fallback."""
        return url.startswith(("http://", "https://"))

    async def extract(self, url: str) -> ExtractionResult:
        """Extract article content from a web page."""
        try:
            import trafilatura

            logger.info(f"[WebPageExtractor] Extracting content from: {url}")

            # Fetch the page (run in thread to avoid blocking)
            downloaded = await asyncio.to_thread(
                trafilatura.fetch_url,
                url,
            )

            if not downloaded:
                logger.warning(f"[WebPageExtractor] Failed to download: {url}")
                return ExtractionResult.failure(
                    error="Failed to download web page",
                    title=self._extract_title_from_url(url),
                )

            # Extract main content
            content = await asyncio.to_thread(
                trafilatura.extract,
                downloaded,
                include_comments=False,
                include_tables=True,
                include_links=False,
                favor_precision=True,
            )

            # Extract metadata
            metadata_result = await asyncio.to_thread(
                trafilatura.extract,
                downloaded,
                output_format="json",
                include_comments=False,
            )

            # Parse metadata
            title = None
            thumbnail_url = None
            site_name = None

            if metadata_result:
                import json

                try:
                    meta = json.loads(metadata_result)
                    title = meta.get("title")
                    site_name = meta.get("sitename")
                except json.JSONDecodeError:
                    pass

            # Try to get OG image for thumbnail
            thumbnail_url = self._extract_og_image(downloaded)

            # Fallback title
            if not title:
                title = self._extract_title_from_html(downloaded) or self._extract_title_from_url(
                    url
                )

            # Truncate content if too long
            if content:
                content = truncate_content(content)

            # Determine content type
            content_type = "article" if content and len(content) > 200 else "link"

            logger.info(
                f"[WebPageExtractor] Extracted: title='{title}', "
                f"content_length={len(content) if content else 0}"
            )

            return ExtractionResult(
                success=True,
                title=title,
                content=content,
                thumbnail_url=thumbnail_url,
                platform="web",
                content_type=content_type,
                metadata={
                    "site_name": site_name,
                    "has_transcript": False,
                },
            )

        except Exception as e:
            logger.error(f"[WebPageExtractor] Error extracting {url}: {e}", exc_info=True)
            return ExtractionResult.failure(
                error=str(e),
                title=self._extract_title_from_url(url),
            )

    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable title from URL path."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if path:
            # Get last path segment
            segments = path.split("/")
            title = segments[-1]
            # Clean up
            title = title.replace("-", " ").replace("_", " ")
            title = title.split(".")[0]  # Remove extension
            return title.title()

        return parsed.netloc

    def _extract_title_from_html(self, html: str) -> Optional[str]:
        """Extract title from HTML."""
        import re

        # Try <title> tag
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
            # Clean up common suffixes
            for suffix in [" - ", " | ", " – ", " :: "]:
                if suffix in title:
                    title = title.split(suffix)[0].strip()
            return title

        # Try og:title
        match = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None

    def _extract_og_image(self, html: str) -> Optional[str]:
        """Extract og:image from HTML."""
        import re

        # Try og:image
        match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()

        # Try twitter:image
        match = re.search(
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()

        return None

