"""Source annotation service for adding page/timestamp markers to content.

This module prepares document content for mindmap generation by adding
source markers that the LLM can preserve in its output, enabling
click-to-navigate functionality.

Example PDF annotation:
    [PAGE:1]
    Introduction and overview...

    [PAGE:2]
    Main topic discussion...

Example video annotation:
    [TIME:00:00]
    Introduction...

    [TIME:05:30]
    Main topic...
"""

import re
from dataclasses import dataclass
from typing import Protocol


@dataclass
class AnnotatedPage:
    """A page of content with source marker."""

    page_number: int
    content: str
    marker: str  # e.g., "[PAGE:1]" or "[TIME:05:30]"


@dataclass
class AnnotatedContent:
    """Content with source annotations."""

    text: str  # Full annotated text
    pages: list[AnnotatedPage]
    source_type: str  # "pdf", "video", "audio", etc.


class PageSource(Protocol):
    """Protocol for page-like sources (PDFs, slides, etc.)."""

    @property
    def page_number(self) -> int:
        """1-indexed page number."""
        ...

    @property
    def content(self) -> str:
        """Page text content."""
        ...


class TimestampedSource(Protocol):
    """Protocol for timestamped sources (videos, audio, podcasts)."""

    @property
    def start_time(self) -> float:
        """Start time in seconds."""
        ...

    @property
    def end_time(self) -> float:
        """End time in seconds."""
        ...

    @property
    def content(self) -> str:
        """Transcript content."""
        ...


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def annotate_pdf_pages(pages: list[PageSource]) -> AnnotatedContent:
    """Annotate PDF pages with [PAGE:X] markers.

    Args:
        pages: List of page objects with page_number and content attributes.

    Returns:
        AnnotatedContent with markers for each page.
    """
    annotated_pages: list[AnnotatedPage] = []
    text_parts: list[str] = []

    for page in pages:
        page_num = page.page_number
        content = page.content.strip()

        if not content:
            continue

        marker = f"[PAGE:{page_num}]"
        annotated_pages.append(AnnotatedPage(
            page_number=page_num,
            content=content,
            marker=marker,
        ))

        # Add marker and content to full text
        text_parts.append(f"{marker}\n{content}")

    return AnnotatedContent(
        text="\n\n".join(text_parts),
        pages=annotated_pages,
        source_type="pdf",
    )


def annotate_video_transcript(
    segments: list[TimestampedSource],
    interval_seconds: int = 30,
) -> AnnotatedContent:
    """Annotate video transcript with [TIME:MM:SS] markers.

    Adds time markers at regular intervals or at segment boundaries.

    Args:
        segments: List of transcript segments with start_time, end_time, content.
        interval_seconds: Minimum interval between time markers.

    Returns:
        AnnotatedContent with time markers.
    """
    annotated_pages: list[AnnotatedPage] = []
    text_parts: list[str] = []
    last_marker_time: float = -interval_seconds  # Ensure first segment gets a marker

    for i, segment in enumerate(segments):
        content = segment.content.strip()
        if not content:
            continue

        start_time = segment.start_time

        # Add marker if enough time has passed since last marker
        if start_time - last_marker_time >= interval_seconds:
            marker = f"[TIME:{format_timestamp(start_time)}]"
            annotated_pages.append(AnnotatedPage(
                page_number=i + 1,  # Use index as "page" number
                content=content,
                marker=marker,
            ))
            text_parts.append(f"{marker}\n{content}")
            last_marker_time = start_time
        else:
            # No new marker, just append content
            text_parts.append(content)

    return AnnotatedContent(
        text="\n\n".join(text_parts),
        pages=annotated_pages,
        source_type="video",
    )


def annotate_plain_text(
    text: str,
    lines_per_page: int = 50,
) -> AnnotatedContent:
    """Annotate plain text by splitting into virtual pages.

    Useful for documents without natural page breaks.

    Args:
        text: Plain text content.
        lines_per_page: Number of lines per virtual "page".

    Returns:
        AnnotatedContent with page markers.
    """
    lines = text.split('\n')
    annotated_pages: list[AnnotatedPage] = []
    text_parts: list[str] = []

    page_num = 1
    for i in range(0, len(lines), lines_per_page):
        page_lines = lines[i:i + lines_per_page]
        content = '\n'.join(page_lines).strip()

        if not content:
            continue

        marker = f"[PAGE:{page_num}]"
        annotated_pages.append(AnnotatedPage(
            page_number=page_num,
            content=content,
            marker=marker,
        ))
        text_parts.append(f"{marker}\n{content}")
        page_num += 1

    return AnnotatedContent(
        text="\n\n".join(text_parts),
        pages=annotated_pages,
        source_type="document",
    )


def remove_annotations(text: str) -> str:
    """Remove source annotations from text.

    Useful for displaying clean text without markers.

    Args:
        text: Text with [PAGE:X] or [TIME:MM:SS] markers.

    Returns:
        Clean text without markers.
    """
    # Remove page markers
    text = re.sub(r'\[PAGE:\d+\]\s*', '', text)
    # Remove time markers
    text = re.sub(r'\[TIME:\d{1,2}:\d{2}(?::\d{2})?\]\s*', '', text)
    return text.strip()
