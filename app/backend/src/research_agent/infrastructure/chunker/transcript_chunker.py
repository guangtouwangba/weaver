"""Transcript chunker.

Chunks video/audio transcripts with timestamp awareness,
preserving temporal context for better retrieval.
"""

import re
from typing import Any

from research_agent.infrastructure.chunker.base import (
    Chunker,
    ChunkResult,
    PageLike,
)
from research_agent.shared.utils.logger import logger


class TranscriptChunker(Chunker):
    """
    Chunker for video/audio transcripts.

    Chunks transcripts while preserving timestamp information
    for accurate video/audio seeking.
    """

    # Common transcript timestamp patterns
    TIMESTAMP_PATTERNS = [
        r"\[(\d{1,2}:\d{2}(?::\d{2})?)\]",  # [MM:SS] or [HH:MM:SS]
        r"(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–]\s*",  # MM:SS - or HH:MM:SS -
        r"\((\d{1,2}:\d{2}(?::\d{2})?)\)",  # (MM:SS) or (HH:MM:SS)
    ]

    CHARS_PER_CHUNK = 500  # Smaller chunks for transcripts

    def supported_mime_types(self) -> list[str]:
        return ["text/vtt", "text/srt", "application/x-subrip"]

    def supported_extensions(self) -> list[str]:
        return [".vtt", ".srt", ".transcript"]

    def chunk_pages(
        self,
        pages: list[PageLike],
    ) -> ChunkResult:
        """Chunk transcript pages."""
        full_text = "\n".join([page.content for page in pages])
        return self.chunk_text(full_text, {"source": "pages"})

    def _parse_timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert timestamp string to seconds."""
        parts = timestamp.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        return 0.0

    def _extract_timestamps(self, text: str) -> list[tuple[str, float, int]]:
        """
        Extract timestamps from text.

        Returns:
            List of (timestamp_str, seconds, position_in_text)
        """
        timestamps = []

        for pattern in self.TIMESTAMP_PATTERNS:
            for match in re.finditer(pattern, text):
                ts_str = match.group(1)
                seconds = self._parse_timestamp_to_seconds(ts_str)
                timestamps.append((ts_str, seconds, match.start()))

        return sorted(timestamps, key=lambda x: x[2])

    def chunk_text(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> ChunkResult:
        """
        Chunk transcript text with timestamp awareness.

        Tries to break at timestamp boundaries when possible.
        """
        if not text.strip():
            return ChunkResult(
                chunks=[],
                chunker_name=self.chunker_name,
                strategy_used="transcript_timestamps",
            )

        base_metadata = metadata or {}
        chunks = []
        chunk_index = 0

        # Extract timestamps
        timestamps = self._extract_timestamps(text)

        if not timestamps:
            # No timestamps found, use simple character-based chunking
            logger.info("[TranscriptChunker] No timestamps found, using simple chunking")
            return self._simple_chunk(text, base_metadata)

        # Chunk at timestamp boundaries
        text_length = len(text)
        current_pos = 0
        current_chunk_start = 0
        first_timestamp_in_chunk = None
        last_timestamp_in_chunk = None

        for ts_str, ts_seconds, ts_pos in timestamps:
            # If adding this segment would exceed chunk size
            if (
                ts_pos - current_chunk_start > self.CHARS_PER_CHUNK
                and current_pos > current_chunk_start
            ):
                # Create chunk from current_chunk_start to current_pos
                chunk_text = text[current_chunk_start:current_pos].strip()
                if chunk_text:
                    chunks.append(
                        {
                            "chunk_index": chunk_index,
                            "content": chunk_text,
                            "page_number": 1,
                            "metadata": {
                                **base_metadata,
                                "chunk_type": "transcript",
                                "start_timestamp": first_timestamp_in_chunk,
                                "end_timestamp": last_timestamp_in_chunk,
                            },
                        }
                    )
                    chunk_index += 1

                current_chunk_start = current_pos
                first_timestamp_in_chunk = ts_str

            if first_timestamp_in_chunk is None:
                first_timestamp_in_chunk = ts_str
            last_timestamp_in_chunk = ts_str
            current_pos = ts_pos

        # Add remaining text
        if current_chunk_start < text_length:
            chunk_text = text[current_chunk_start:].strip()
            if chunk_text:
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": chunk_text,
                        "page_number": 1,
                        "metadata": {
                            **base_metadata,
                            "chunk_type": "transcript",
                            "start_timestamp": first_timestamp_in_chunk,
                            "end_timestamp": last_timestamp_in_chunk,
                        },
                    }
                )

        logger.info(
            f"[TranscriptChunker] Created {len(chunks)} chunks from "
            f"{len(timestamps)} timestamps"
        )

        return ChunkResult(
            chunks=chunks,
            chunker_name=self.chunker_name,
            strategy_used="transcript_timestamps",
        )

    def _simple_chunk(
        self,
        text: str,
        base_metadata: dict[str, Any],
    ) -> ChunkResult:
        """Simple character-based chunking fallback."""
        chunks = []
        chunk_index = 0

        for i in range(0, len(text), self.CHARS_PER_CHUNK):
            chunk_text = text[i : i + self.CHARS_PER_CHUNK].strip()
            if chunk_text:
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": chunk_text,
                        "page_number": 1,
                        "metadata": {**base_metadata, "chunk_type": "transcript_simple"},
                    }
                )
                chunk_index += 1

        return ChunkResult(
            chunks=chunks,
            chunker_name=self.chunker_name,
            strategy_used="transcript_simple",
        )
