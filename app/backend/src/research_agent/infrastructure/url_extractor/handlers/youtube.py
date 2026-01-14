"""YouTube video content extractor using youtube-transcript-api.

Falls back to Gemini audio transcription when no transcript is available.
"""

import re

from research_agent.infrastructure.url_extractor.base import ExtractionResult, URLExtractor
from research_agent.infrastructure.url_extractor.handlers.youtube_retry import (
    execute_youtube_api_call,
)
from research_agent.infrastructure.url_extractor.utils import (
    PLATFORM_PATTERNS,
    truncate_content,
)
from research_agent.shared.utils.logger import logger


class YouTubeExtractor(URLExtractor):
    """Extractor for YouTube videos.

    Uses a two-stage transcript extraction:
    1. Try youtube-transcript-api for existing subtitles
    2. Fall back to Gemini audio transcription if no subtitles available

    This ensures transcripts are extracted at upload time, avoiding
    repeated downloads during content generation.
    """

    @property
    def platform(self) -> str:
        return "youtube"

    def can_handle(self, url: str) -> bool:
        """Check if URL is a YouTube video."""
        for pattern in PLATFORM_PATTERNS.get("youtube", []):
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def _extract_video_id(self, url: str) -> str | None:
        """Extract video ID from YouTube URL."""
        for pattern in PLATFORM_PATTERNS.get("youtube", []):
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    async def extract(self, url: str) -> ExtractionResult:
        """Extract transcript and metadata from YouTube video.

        Extraction strategy:
        1. Get video metadata via oEmbed API
        2. Try to get transcript from YouTube's built-in subtitles
        3. If no subtitles available, fall back to Gemini audio transcription
        """
        video_id = self._extract_video_id(url)
        if not video_id:
            return ExtractionResult.failure(
                error="Could not extract video ID from URL",
                title=url,
            )

        logger.info(f"[YouTubeExtractor] Extracting video: {video_id}")

        try:
            # Get video metadata first
            metadata = await self._get_video_metadata(video_id)

            # Step 1: Try to get transcript from YouTube's subtitles
            transcript_text, has_transcript = await self._get_transcript(video_id)
            transcript_source = "youtube_subtitles" if has_transcript else None

            # Step 2: Fall back to Gemini audio transcription if no subtitles
            if not has_transcript or not transcript_text:
                logger.info(
                    f"[YouTubeExtractor] No YouTube subtitles for {video_id}, "
                    "attempting Gemini audio transcription..."
                )
                gemini_transcript = await self._transcribe_with_gemini(video_id)
                if gemini_transcript:
                    transcript_text = gemini_transcript
                    has_transcript = True
                    transcript_source = "gemini_audio"
                    logger.info(
                        f"[YouTubeExtractor] Gemini transcription successful: "
                        f"{len(gemini_transcript)} chars"
                    )

            # Build thumbnail URL
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"

            # Truncate transcript if too long
            if transcript_text:
                transcript_text = truncate_content(transcript_text)

            result = ExtractionResult(
                success=True,
                title=metadata.get("title", f"YouTube Video ({video_id})"),
                content=transcript_text,
                thumbnail_url=thumbnail_url,
                platform="youtube",
                content_type="video",
                metadata={
                    "video_id": video_id,
                    "channel_name": metadata.get("channel_name"),
                    "duration": metadata.get("duration"),
                    "has_transcript": has_transcript,
                    "transcript_source": transcript_source,
                    "view_count": metadata.get("view_count"),
                },
            )

            logger.info(
                f"[YouTubeExtractor] Extracted: title='{result.title}', "
                f"transcript_length={len(transcript_text) if transcript_text else 0}, "
                f"has_transcript={has_transcript}, source={transcript_source}"
            )

            return result

        except Exception as e:
            logger.error(f"[YouTubeExtractor] Error extracting {video_id}: {e}", exc_info=True)
            return ExtractionResult.failure(
                error=str(e),
                title=f"YouTube Video ({video_id})",
            )

    async def _get_transcript(self, video_id: str) -> tuple[str | None, bool]:
        """
        Get transcript for a YouTube video.

        Supports youtube-transcript-api v1.x (new API).

        Tries multiple approaches:
        1. First try specific languages (Chinese, English, etc.)
        2. If that fails, try to list all available transcripts and pick the best one

        Returns:
            Tuple of (transcript_text, has_transcript).
        """
        import asyncio

        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._proxy_config import GenericProxyConfig

            from research_agent.config import get_settings

            settings = get_settings()

            # Configure proxy if available
            proxy_config = None
            if settings.youtube_proxy_url:
                logger.info("[YouTubeExtractor] Using proxy for transcript API")
                proxy_config = GenericProxyConfig(
                    http_proxy=settings.youtube_proxy_url,
                    https_proxy=settings.youtube_proxy_url,
                )

            # Create API instance (v1.x requires instantiation)
            ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config) if proxy_config else YouTubeTranscriptApi()

            # Preferred languages in order of priority
            preferred_languages = ("zh-Hans", "zh-Hant", "zh", "en", "ja", "ko")

            # Try 1: Direct fetch with preferred languages
            try:
                def fetch_transcript():
                    return ytt_api.fetch(video_id, languages=preferred_languages)

                result, success = await execute_youtube_api_call(
                    func=fetch_transcript,
                    operation_name=f"fetch transcript for {video_id}",
                    max_retries=2,
                )

                if success and result:
                    # Convert FetchedTranscript to list of dicts
                    transcript_list = [
                        {"text": s.text, "start": s.start, "duration": s.duration} for s in result
                    ]
                    text = self._format_transcript(transcript_list)
                    if text:
                        logger.info(
                            f"[YouTubeExtractor] Got transcript with preferred languages for {video_id}"
                        )
                        return text, True
            except Exception as e:
                error_str = str(e)
                if "NoTranscriptFound" in error_str or "No transcripts were found" in error_str:
                    logger.debug(
                        f"[YouTubeExtractor] No transcript in preferred languages for {video_id}"
                    )
                else:
                    logger.warning(f"[YouTubeExtractor] Error fetching transcript: {e}")

            # Try 2: List all transcripts and pick the best one
            try:
                def list_transcripts():
                    return ytt_api.list(video_id)

                transcript_list_obj, success = await execute_youtube_api_call(
                    func=list_transcripts,
                    operation_name=f"list transcripts for {video_id}",
                    max_retries=2,
                )

                if not success or not transcript_list_obj:
                    return None, False

                # Try manually created transcripts first
                for transcript_info in transcript_list_obj:
                    if not transcript_info.is_generated:
                        logger.info(
                            f"[YouTubeExtractor] Found manual transcript in {transcript_info.language_code}"
                        )
                        fetched = await asyncio.to_thread(transcript_info.fetch)
                        transcript_list = [
                            {"text": s.text, "start": s.start, "duration": s.duration}
                            for s in fetched
                        ]
                        text = self._format_transcript(transcript_list)
                        if text:
                            return text, True

                # Fall back to auto-generated transcripts
                for transcript_info in transcript_list_obj:
                    if transcript_info.is_generated:
                        logger.info(
                            f"[YouTubeExtractor] Found auto-generated transcript in {transcript_info.language_code}"
                        )
                        fetched = await asyncio.to_thread(transcript_info.fetch)
                        transcript_list = [
                            {"text": s.text, "start": s.start, "duration": s.duration}
                            for s in fetched
                        ]
                        text = self._format_transcript(transcript_list)
                        if text:
                            return text, True

            except Exception as e:
                error_str = str(e)
                if "TranscriptsDisabled" in error_str:
                    logger.warning(f"[YouTubeExtractor] Transcripts are disabled for {video_id}")
                    return None, False
                elif "NoTranscriptFound" in error_str:
                    logger.warning(f"[YouTubeExtractor] No transcripts found at all for {video_id}")
                    return None, False
                else:
                    logger.warning(f"[YouTubeExtractor] Error listing transcripts: {e}")

        except ImportError:
            logger.error("[YouTubeExtractor] youtube-transcript-api not installed")
            return None, False
        except Exception as e:
            logger.warning(f"[YouTubeExtractor] Failed to get transcript for {video_id}: {e}")
            return None, False

        logger.warning(f"[YouTubeExtractor] No usable transcript found for {video_id}")
        return None, False

    def _format_transcript(self, transcript_list: list[dict]) -> str:
        """Format transcript segments into readable paragraphs with time markers.

        Adds [TIME:MM:SS] markers at the start of each paragraph to enable
        source linking in mindmap nodes.
        """
        if not transcript_list:
            return ""

        def format_time(seconds: float) -> str:
            """Format seconds as MM:SS or HH:MM:SS."""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            return f"{minutes:02d}:{secs:02d}"

        # Group by natural paragraph breaks (longer pauses)
        paragraphs = []
        current_paragraph = []
        paragraph_start_time = 0
        last_end = 0

        for segment in transcript_list:
            text = segment.get("text", "").strip()
            if not text:
                continue

            start = segment.get("start", 0)

            # New paragraph if pause > 2 seconds
            if current_paragraph and (start - last_end) > 2:
                # Add time marker at start of paragraph
                time_marker = f"[TIME:{format_time(paragraph_start_time)}]"
                paragraph_text = " ".join(current_paragraph)
                paragraphs.append(f"{time_marker}\n{paragraph_text}")
                current_paragraph = []
                paragraph_start_time = start

            if not current_paragraph:
                paragraph_start_time = start

            current_paragraph.append(text)
            last_end = start + segment.get("duration", 0)

        # Add remaining paragraph
        if current_paragraph:
            time_marker = f"[TIME:{format_time(paragraph_start_time)}]"
            paragraph_text = " ".join(current_paragraph)
            paragraphs.append(f"{time_marker}\n{paragraph_text}")

        return "\n\n".join(paragraphs)

    async def _get_video_metadata(self, video_id: str) -> dict:
        """
        Get video metadata using oEmbed API (no API key required).

        Returns:
            Dict with title, channel_name, etc.
        """

        import httpx

        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(oembed_url)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "title": data.get("title"),
                        "channel_name": data.get("author_name"),
                    }
        except Exception as e:
            logger.warning(f"[YouTubeExtractor] Failed to get oEmbed metadata: {e}")

        return {}

    async def _transcribe_with_gemini(self, video_id: str) -> str | None:
        """
        Transcribe video audio using Gemini when no YouTube subtitles are available.

        This is called during URL extraction (upload time) to ensure transcripts
        are available immediately, avoiding repeated downloads during content generation.

        Args:
            video_id: YouTube video ID

        Returns:
            Transcript text with [TIME:MM:SS] markers, or None if transcription fails
        """
        try:
            from research_agent.config import get_settings
            from research_agent.infrastructure.llm.gemini_audio import transcribe_youtube_video

            settings = get_settings()

            # Check if OpenRouter API key is available
            if not settings.openrouter_api_key:
                logger.warning(
                    "[YouTubeExtractor] OpenRouter API key not configured, "
                    "skipping Gemini audio transcription"
                )
                return None

            result = await transcribe_youtube_video(
                video_id=video_id,
                api_key=settings.openrouter_api_key,
                max_duration_minutes=settings.gemini_audio_max_duration_minutes,
            )

            if result.success and result.transcript:
                return result.transcript
            else:
                logger.warning(
                    f"[YouTubeExtractor] Gemini transcription failed: {result.error}"
                )
                return None

        except ImportError as e:
            logger.warning(f"[YouTubeExtractor] Gemini audio module not available: {e}")
            return None
        except Exception as e:
            logger.error(
                f"[YouTubeExtractor] Error during Gemini transcription: {e}",
                exc_info=True
            )
            return None
