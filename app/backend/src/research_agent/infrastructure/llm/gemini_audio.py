"""Audio transcription service using Gemini via OpenRouter.

This module provides audio-to-text transcription for YouTube videos
that don't have available subtitles, using Gemini's multimodal capabilities.
"""

import asyncio
import base64
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from research_agent.shared.utils.logger import logger


@dataclass
class TranscriptionResult:
    """Result of audio transcription."""

    success: bool
    transcript: Optional[str] = None  # Transcript with [TIME:MM:SS] markers
    duration_seconds: Optional[float] = None
    error: Optional[str] = None

    @classmethod
    def failure(cls, error: str) -> "TranscriptionResult":
        return cls(success=False, error=error)


class GeminiAudioTranscriber:
    """Transcribe audio using Gemini via OpenRouter.

    Features:
    - Downloads YouTube audio using yt-dlp
    - Transcribes using Gemini's multimodal capabilities
    - Returns transcript with [TIME:MM:SS] markers
    - Automatic temp file cleanup

    Usage:
        transcriber = GeminiAudioTranscriber(openrouter_api_key)
        result = await transcriber.transcribe_youtube(video_id)
        if result.success:
            print(result.transcript)
    """

    # Gemini model for audio transcription
    TRANSCRIPTION_MODEL = "google/gemini-2.0-flash-001"

    # Max duration in seconds (60 minutes / 1 hour)
    MAX_DURATION_SECONDS = 60 * 60

    # Token rate: ~32 tokens per second of audio
    TOKENS_PER_SECOND = 32

    def __init__(self, api_key: str, max_duration_seconds: int = MAX_DURATION_SECONDS):
        self._api_key = api_key
        self._max_duration = max_duration_seconds

    async def transcribe_youtube(self, video_id: str) -> TranscriptionResult:
        """Transcribe a YouTube video's audio.

        Args:
            video_id: YouTube video ID (e.g., "kVniOF36GEk")

        Returns:
            TranscriptionResult with transcript containing [TIME:MM:SS] markers
        """
        logger.info(f"[GeminiTranscriber] Starting transcription for video: {video_id}")

        # Step 1: Download audio
        audio_path, duration = await self._download_audio(video_id)
        if not audio_path:
            return TranscriptionResult.failure("Failed to download audio")

        try:
            # Check duration limit
            if duration and duration > self._max_duration:
                return TranscriptionResult.failure(
                    f"Video too long: {duration/60:.1f} minutes (max: {self._max_duration/60:.0f} minutes)"
                )

            # Step 2: Read and encode audio
            audio_base64 = await self._encode_audio(audio_path)
            if not audio_base64:
                return TranscriptionResult.failure("Failed to encode audio")

            # Step 3: Send to Gemini for transcription
            transcript = await self._transcribe_with_gemini(audio_base64, duration)
            if not transcript:
                return TranscriptionResult.failure("Gemini transcription failed")

            logger.info(
                f"[GeminiTranscriber] Transcription complete: "
                f"{len(transcript)} chars, {duration:.0f}s duration"
            )

            return TranscriptionResult(
                success=True,
                transcript=transcript,
                duration_seconds=duration,
            )

        finally:
            # Cleanup temp file
            await self._cleanup(audio_path)

    async def _download_audio(self, video_id: str) -> tuple[Optional[Path], Optional[float]]:
        """Download audio from YouTube using yt-dlp.

        Returns:
            Tuple of (audio_path, duration_seconds) or (None, None) on failure
        """
        try:
            import yt_dlp

            from research_agent.config import get_settings
        except ImportError:
            logger.error("[GeminiTranscriber] yt-dlp not installed. Run: pip install yt-dlp")
            return None, None

        settings = get_settings()

        # Create temp file
        temp_dir = tempfile.mkdtemp(prefix="gemini_audio_")
        output_path = Path(temp_dir) / f"{video_id}.mp3"

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(output_path.with_suffix("")),  # yt-dlp adds extension
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "128",  # Lower quality = smaller file
                }
            ],
            "quiet": True,
            "no_warnings": True,
            # Explicitly specify ffmpeg location (searches common paths)
            "ffmpeg_location": "/usr/bin",
        }

        # Add cookies if configured
        cookie_temp_path: Optional[Path] = None
        try:
            if settings.youtube_cookies_path:
                cookies_path = Path(settings.youtube_cookies_path)
                if cookies_path.exists():
                    logger.info(f"[GeminiTranscriber] Using cookies from file: {cookies_path}")
                    ydl_opts["cookiefile"] = str(cookies_path)
                else:
                    logger.warning(
                        f"[GeminiTranscriber] Configured cookies file not found: {cookies_path}"
                    )
            elif settings.youtube_cookies_content:
                # Create temp cookie file
                cookie_temp_file = tempfile.NamedTemporaryFile(
                    mode="w",
                    delete=False,
                    prefix="youtube_cookies_",
                    suffix=".txt",
                )

                content = settings.youtube_cookies_content
                if not content.startswith("# Netscape"):
                    logger.info(
                        "[GeminiTranscriber] Converting cookies from Header format to Netscape format"
                    )
                    cookies = []
                    # Helper to convert header format to Netscape format
                    raw_cookies = [c.strip() for c in content.split(";") if c.strip()]
                    for cookie in raw_cookies:
                        if "=" not in cookie:
                            continue
                        name, value = cookie.split("=", 1)
                        # Netscape format: domain flag path secure expiration name value
                        cookies.append(f".youtube.com\tTRUE\t/\tTRUE\t2147483647\t{name}\t{value}")
                    content = "# Netscape HTTP Cookie File\n" + "\n".join(cookies) + "\n"

                cookie_temp_file.write(content)
                cookie_temp_file.close()
                cookie_temp_path = Path(cookie_temp_file.name)
                logger.info("[GeminiTranscriber] Using cookies provided via environment variable")
                ydl_opts["cookiefile"] = str(cookie_temp_path)

            url = f"https://www.youtube.com/watch?v={video_id}"

            try:
                logger.info(f"[GeminiTranscriber] Downloading audio: {video_id}")

                # Run yt-dlp in executor to avoid blocking
                loop = asyncio.get_event_loop()

                def download():
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        return info.get("duration", 0)

                duration = await loop.run_in_executor(None, download)

                # Find the actual output file (yt-dlp may add/change extension)
                for file in Path(temp_dir).glob(f"{video_id}.*"):
                    if file.suffix in (".mp3", ".m4a", ".webm", ".opus"):
                        logger.info(f"[GeminiTranscriber] Downloaded: {file}, duration={duration}s")
                        return file, duration

                logger.error(f"[GeminiTranscriber] Audio file not found after download")
                return None, None

            except Exception as e:
                logger.error(f"[GeminiTranscriber] Download failed: {e}")
                return None, None

        finally:
            # Cleanup temp cookie file if created
            if cookie_temp_path and cookie_temp_path.exists():
                try:
                    cookie_temp_path.unlink()
                except Exception as e:
                    logger.warning(f"[GeminiTranscriber] Failed to cleanup temp cookie file: {e}")

    async def _encode_audio(self, audio_path: Path) -> Optional[str]:
        """Read and base64 encode audio file."""
        try:
            loop = asyncio.get_event_loop()

            def read_and_encode():
                with open(audio_path, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")

            encoded = await loop.run_in_executor(None, read_and_encode)

            # Log size for debugging
            size_mb = len(encoded) * 3 / 4 / 1024 / 1024  # Approximate decoded size
            logger.info(f"[GeminiTranscriber] Audio encoded: ~{size_mb:.1f} MB")

            return encoded

        except Exception as e:
            logger.error(f"[GeminiTranscriber] Encode failed: {e}")
            return None

    async def _transcribe_with_gemini(
        self, audio_base64: str, duration: Optional[float]
    ) -> Optional[str]:
        """Send audio to Gemini for transcription via OpenRouter."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=self._api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        # Estimate tokens for logging
        estimated_tokens = int((duration or 0) * self.TOKENS_PER_SECOND)
        logger.info(
            f"[GeminiTranscriber] Sending to Gemini: " f"~{estimated_tokens} tokens estimated"
        )

        # Build multimodal message
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """请完整转录这段音频内容。

要求：
1. 在每个自然段落开头添加时间标记 [TIME:MM:SS]
2. 时间标记应该反映该段落开始的大致时间
3. 保持原始语言（不要翻译）
4. 忽略背景音乐和噪音
5. 如果有多个说话人，用换行分隔

示例格式：
[TIME:00:00]
大家好，欢迎观看今天的视频...

[TIME:01:30]
今天我们要讨论的主题是...

请开始转录：""",
                    },
                    {"type": "input_audio", "input_audio": {"data": audio_base64, "format": "mp3"}},
                ],
            }
        ]

        try:
            response = await client.chat.completions.create(
                model=self.TRANSCRIPTION_MODEL,
                messages=messages,
            )

            transcript = response.choices[0].message.content

            # Log usage
            if response.usage:
                logger.info(
                    f"[GeminiTranscriber] Gemini usage: "
                    f"prompt={response.usage.prompt_tokens}, "
                    f"completion={response.usage.completion_tokens}"
                )

            return transcript

        except Exception as e:
            logger.error(f"[GeminiTranscriber] Gemini API error: {e}")
            return None

    async def _cleanup(self, audio_path: Path) -> None:
        """Clean up temporary audio file and directory."""
        try:
            if audio_path.exists():
                audio_path.unlink()

            # Remove temp directory if empty
            temp_dir = audio_path.parent
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                temp_dir.rmdir()

            logger.debug(f"[GeminiTranscriber] Cleaned up: {audio_path}")

        except Exception as e:
            logger.warning(f"[GeminiTranscriber] Cleanup failed: {e}")


async def transcribe_youtube_video(
    video_id: str,
    api_key: str,
    max_duration_minutes: int = 30,
) -> TranscriptionResult:
    """Convenience function to transcribe a YouTube video.

    Args:
        video_id: YouTube video ID
        api_key: OpenRouter API key
        max_duration_minutes: Maximum video duration in minutes

    Returns:
        TranscriptionResult with transcript containing [TIME:MM:SS] markers
    """
    transcriber = GeminiAudioTranscriber(
        api_key=api_key,
        max_duration_seconds=max_duration_minutes * 60,
    )
    return await transcriber.transcribe_youtube(video_id)
