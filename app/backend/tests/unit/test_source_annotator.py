"""Unit tests for source annotation service."""

import pytest
from dataclasses import dataclass
from research_agent.domain.services.source_annotator import (
    annotate_pdf_pages,
    annotate_video_transcript,
    annotate_plain_text,
    format_timestamp,
    remove_annotations,
)


@dataclass
class MockPage:
    """Mock page for testing."""
    page_number: int
    content: str


@dataclass
class MockSegment:
    """Mock transcript segment for testing."""
    start_time: float
    end_time: float
    content: str


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_formats_minutes_seconds(self):
        """Should format seconds as MM:SS."""
        assert format_timestamp(65) == "01:05"
        assert format_timestamp(0) == "00:00"
        assert format_timestamp(59) == "00:59"

    def test_formats_hours(self):
        """Should format with hours when >= 1 hour."""
        assert format_timestamp(3600) == "01:00:00"
        assert format_timestamp(3665) == "01:01:05"
        assert format_timestamp(7200) == "02:00:00"


class TestAnnotatePdfPages:
    """Tests for annotate_pdf_pages function."""

    def test_annotates_single_page(self):
        """Should annotate a single page."""
        pages = [MockPage(page_number=1, content="Hello world")]
        result = annotate_pdf_pages(pages)
        
        assert result.source_type == "pdf"
        assert "[PAGE:1]" in result.text
        assert "Hello world" in result.text
        assert len(result.pages) == 1

    def test_annotates_multiple_pages(self):
        """Should annotate multiple pages."""
        pages = [
            MockPage(page_number=1, content="Page one"),
            MockPage(page_number=2, content="Page two"),
            MockPage(page_number=3, content="Page three"),
        ]
        result = annotate_pdf_pages(pages)
        
        assert "[PAGE:1]" in result.text
        assert "[PAGE:2]" in result.text
        assert "[PAGE:3]" in result.text
        assert len(result.pages) == 3

    def test_skips_empty_pages(self):
        """Should skip pages with empty content."""
        pages = [
            MockPage(page_number=1, content="Content"),
            MockPage(page_number=2, content=""),
            MockPage(page_number=3, content="More content"),
        ]
        result = annotate_pdf_pages(pages)
        
        assert "[PAGE:1]" in result.text
        assert "[PAGE:2]" not in result.text
        assert "[PAGE:3]" in result.text
        assert len(result.pages) == 2


class TestAnnotateVideoTranscript:
    """Tests for annotate_video_transcript function."""

    def test_annotates_transcript_segments(self):
        """Should annotate transcript with time markers."""
        segments = [
            MockSegment(start_time=0, end_time=30, content="Introduction"),
            MockSegment(start_time=30, end_time=60, content="Main topic"),
        ]
        result = annotate_video_transcript(segments, interval_seconds=30)
        
        assert result.source_type == "video"
        assert "[TIME:00:00]" in result.text
        assert "[TIME:00:30]" in result.text
        assert "Introduction" in result.text
        assert "Main topic" in result.text

    def test_respects_interval(self):
        """Should not add markers more frequently than interval."""
        segments = [
            MockSegment(start_time=0, end_time=10, content="Part 1"),
            MockSegment(start_time=10, end_time=20, content="Part 2"),
            MockSegment(start_time=20, end_time=30, content="Part 3"),
        ]
        result = annotate_video_transcript(segments, interval_seconds=30)
        
        # Only first segment should have marker
        assert result.text.count("[TIME:") == 1

    def test_handles_long_timestamps(self):
        """Should format hour timestamps correctly."""
        segments = [
            MockSegment(start_time=3600, end_time=3630, content="After one hour"),
        ]
        result = annotate_video_transcript(segments, interval_seconds=30)
        
        assert "[TIME:01:00:00]" in result.text


class TestAnnotatePlainText:
    """Tests for annotate_plain_text function."""

    def test_splits_by_lines(self):
        """Should split text into virtual pages."""
        text = "\n".join([f"Line {i}" for i in range(100)])
        result = annotate_plain_text(text, lines_per_page=50)
        
        assert result.source_type == "document"
        assert "[PAGE:1]" in result.text
        assert "[PAGE:2]" in result.text
        assert len(result.pages) == 2

    def test_handles_short_text(self):
        """Should handle text shorter than one page."""
        text = "Short text\nWith few lines"
        result = annotate_plain_text(text, lines_per_page=50)
        
        assert "[PAGE:1]" in result.text
        assert len(result.pages) == 1


class TestRemoveAnnotations:
    """Tests for remove_annotations function."""

    def test_removes_page_markers(self):
        """Should remove [PAGE:X] markers."""
        text = "[PAGE:1]\nContent here\n\n[PAGE:2]\nMore content"
        result = remove_annotations(text)
        
        assert "[PAGE:" not in result
        assert "Content here" in result
        assert "More content" in result

    def test_removes_time_markers(self):
        """Should remove [TIME:MM:SS] markers."""
        text = "[TIME:00:00]\nIntro\n\n[TIME:05:30]\nMain"
        result = remove_annotations(text)
        
        assert "[TIME:" not in result
        assert "Intro" in result
        assert "Main" in result

    def test_handles_mixed_markers(self):
        """Should remove both page and time markers."""
        text = "[PAGE:1] Content [TIME:10:30] More"
        result = remove_annotations(text)
        
        assert "[PAGE:" not in result
        assert "[TIME:" not in result
        assert "Content" in result
        assert "More" in result
