"""Text locator service for Quote-to-Coordinate mapping.

This module provides functionality to locate quoted text within document
full content, supporting both exact and fuzzy matching. Used for calculating
precise character positions and page numbers for citations.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from research_agent.shared.utils.logger import logger

# Try to import rapidfuzz for fuzzy matching
# Falls back to basic matching if not available
try:
    from rapidfuzz import fuzz, process
    from rapidfuzz.distance import Levenshtein

    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logger.warning(
        "[TextLocator] rapidfuzz not installed. Fuzzy matching will be limited. "
        "Install with: pip install rapidfuzz"
    )


@dataclass
class LocationResult:
    """Result of locating a quote in document text."""

    found: bool
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    page_number: Optional[int] = None
    match_score: float = 0.0
    matched_text: Optional[str] = None  # The actual text that was matched
    match_type: str = "none"  # "exact", "fuzzy", "partial", "none"


class TextLocator:
    """
    Service for locating quoted text within document content.

    Implements Quote-to-Coordinate strategy:
    1. Try exact match first (fastest)
    2. Try fuzzy matching with rapidfuzz
    3. Try partial/substring matching as fallback
    """

    def __init__(self, fuzzy_threshold: int = 85):
        """
        Initialize TextLocator.

        Args:
            fuzzy_threshold: Minimum fuzzy match score (0-100) to consider a match
        """
        self.fuzzy_threshold = fuzzy_threshold

    def locate(
        self,
        full_text: str,
        quote: str,
        page_map: Optional[List[Dict[str, Any]]] = None,
    ) -> LocationResult:
        """
        Locate a quote within the full document text.

        Args:
            full_text: Complete document text
            quote: Text fragment to locate
            page_map: Optional list of page boundaries from parsing_metadata
                      Format: [{"page": 1, "start": 0, "end": 1500}, ...]

        Returns:
            LocationResult with position and page information
        """
        if not quote or not full_text:
            return LocationResult(found=False, match_type="none")

        # Normalize whitespace for matching
        normalized_quote = self._normalize_whitespace(quote)
        normalized_text = self._normalize_whitespace(full_text)

        # Strategy 1: Exact match
        result = self._try_exact_match(full_text, quote)
        if result.found:
            if page_map:
                result.page_number = self._calculate_page(page_map, result.char_start)
            return result

        # Try with normalized text
        result = self._try_exact_match(normalized_text, normalized_quote)
        if result.found:
            # Map back to original positions (approximate)
            original_pos = self._find_original_position(
                full_text, normalized_text, result.char_start
            )
            if original_pos is not None:
                result.char_start = original_pos
                result.char_end = original_pos + len(quote)
            if page_map:
                result.page_number = self._calculate_page(page_map, result.char_start)
            return result

        # Strategy 2: Fuzzy match (if rapidfuzz available)
        if RAPIDFUZZ_AVAILABLE:
            result = self._try_fuzzy_match(full_text, quote)
            if result.found:
                if page_map:
                    result.page_number = self._calculate_page(page_map, result.char_start)
                return result

        # Strategy 3: Partial/substring match
        result = self._try_partial_match(full_text, quote)
        if result.found:
            if page_map:
                result.page_number = self._calculate_page(page_map, result.char_start)
            return result

        return LocationResult(found=False, match_type="none")

    def _try_exact_match(self, text: str, quote: str) -> LocationResult:
        """Try exact substring match."""
        start = text.find(quote)
        if start != -1:
            return LocationResult(
                found=True,
                char_start=start,
                char_end=start + len(quote),
                match_score=100.0,
                matched_text=quote,
                match_type="exact",
            )
        return LocationResult(found=False)

    def _try_fuzzy_match(self, text: str, quote: str) -> LocationResult:
        """Try fuzzy matching using rapidfuzz."""
        if not RAPIDFUZZ_AVAILABLE:
            return LocationResult(found=False)

        # Split text into sentences or chunks for matching
        sentences = self._split_into_sentences(text)

        if not sentences:
            return LocationResult(found=False)

        # Find best matching sentence
        best_match = process.extractOne(
            quote,
            sentences,
            scorer=fuzz.ratio,
            score_cutoff=self.fuzzy_threshold,
        )

        if best_match:
            matched_text, score, index = best_match
            # Find position of matched sentence in original text
            start = text.find(matched_text)
            if start != -1:
                return LocationResult(
                    found=True,
                    char_start=start,
                    char_end=start + len(matched_text),
                    match_score=score,
                    matched_text=matched_text,
                    match_type="fuzzy",
                )

        # Try partial ratio for substring matches
        best_partial = process.extractOne(
            quote,
            sentences,
            scorer=fuzz.partial_ratio,
            score_cutoff=self.fuzzy_threshold,
        )

        if best_partial:
            matched_text, score, index = best_partial
            start = text.find(matched_text)
            if start != -1:
                return LocationResult(
                    found=True,
                    char_start=start,
                    char_end=start + len(matched_text),
                    match_score=score,
                    matched_text=matched_text,
                    match_type="fuzzy_partial",
                )

        return LocationResult(found=False)

    def _try_partial_match(self, text: str, quote: str) -> LocationResult:
        """Try partial matching - find if significant portion of quote exists."""
        # Try finding a significant substring (first/last 50 chars)
        min_length = min(50, len(quote) // 2)

        # Try first part
        if len(quote) > min_length:
            first_part = quote[:min_length]
            start = text.find(first_part)
            if start != -1:
                # Check how much of the quote matches from this position
                end = start + len(quote)
                if end <= len(text):
                    actual_text = text[start:end]
                    if RAPIDFUZZ_AVAILABLE:
                        score = fuzz.ratio(quote, actual_text)
                    else:
                        # Simple similarity check
                        score = self._simple_similarity(quote, actual_text)

                    if score >= self.fuzzy_threshold:
                        return LocationResult(
                            found=True,
                            char_start=start,
                            char_end=end,
                            match_score=score,
                            matched_text=actual_text,
                            match_type="partial",
                        )

        return LocationResult(found=False)

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for matching."""
        # Split on sentence-ending punctuation
        # Handle both English and Chinese punctuation
        pattern = r"[.!?。！？]\s*|\n\n+"
        sentences = re.split(pattern, text)
        # Filter out empty strings and very short sentences
        return [s.strip() for s in sentences if s and len(s.strip()) > 10]

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        return " ".join(text.split())

    def _find_original_position(
        self, original: str, normalized: str, norm_pos: int
    ) -> Optional[int]:
        """Map position from normalized text back to original."""
        # This is an approximation - count non-whitespace chars
        norm_count = 0
        for i, char in enumerate(original):
            if not char.isspace():
                if norm_count == norm_pos:
                    return i
                norm_count += 1
            elif norm_count > 0:
                norm_count += 1  # Single space in normalized
        return None

    def _calculate_page(self, page_map: List[Dict[str, Any]], char_start: int) -> Optional[int]:
        """Calculate page number from character position using page map."""
        if not page_map or char_start is None:
            return None

        for entry in page_map:
            page = entry.get("page", 0)
            start = entry.get("start", 0)
            end = entry.get("end", 0)

            if start <= char_start < end:
                return page

        # If not found, return last page
        if page_map:
            return page_map[-1].get("page", 0)

        return None

    def _simple_similarity(self, s1: str, s2: str) -> float:
        """Simple similarity calculation without rapidfuzz."""
        if not s1 or not s2:
            return 0.0
        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(s1, s2))
        return (matches / max(len(s1), len(s2))) * 100


# Convenience functions


def locate_citation_in_document(
    full_text: str,
    quote: str,
    page_map: Optional[List[Dict[str, Any]]] = None,
    threshold: int = 85,
) -> Tuple[Optional[int], Optional[int], float]:
    """
    Locate a quote in document text.

    Args:
        full_text: Complete document text
        quote: Text fragment to locate
        page_map: Optional page boundaries from parsing_metadata
        threshold: Fuzzy match threshold (0-100)

    Returns:
        Tuple of (char_start, char_end, match_score)
        Returns (None, None, 0.0) if not found
    """
    locator = TextLocator(fuzzy_threshold=threshold)
    result = locator.locate(full_text, quote, page_map)

    if result.found:
        return result.char_start, result.char_end, result.match_score
    return None, None, 0.0


def calculate_page_number(page_map: List[Dict[str, Any]], char_start: int) -> Optional[int]:
    """
    Calculate page number from character position.

    Args:
        page_map: Page boundaries from parsing_metadata
                  Format: [{"page": 1, "start": 0, "end": 1500}, ...]
        char_start: Character position to look up

    Returns:
        Page number or None if not found
    """
    locator = TextLocator()
    return locator._calculate_page(page_map, char_start)
