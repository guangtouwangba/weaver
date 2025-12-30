"""Utility functions for document parsing.

This module provides helper functions for analyzing parsed document content,
including detection of scanned PDFs that may need OCR processing.
"""

import re
from typing import TYPE_CHECKING

from research_agent.shared.utils.logger import logger

if TYPE_CHECKING:
    from research_agent.infrastructure.parser.base import ParseResult


def is_scanned_pdf(
    parse_result: "ParseResult",
    min_chars_per_page: int = 100,
    max_garbage_ratio: float = 0.3,
) -> bool:
    """
    Detect if a PDF is scanned (image-based) and needs OCR.

    This function analyzes the parsed content to determine if the PDF
    is likely a scanned document based on:
    1. Average character count per page (too few suggests images)
    2. Ratio of garbage/non-standard characters (high ratio suggests OCR artifacts)

    Args:
        parse_result: The result from initial parsing attempt.
        min_chars_per_page: Minimum average characters per page to consider as text PDF.
        max_garbage_ratio: Maximum ratio of garbage characters before triggering OCR.

    Returns:
        True if the PDF appears to be scanned and needs OCR, False otherwise.
    """
    if not parse_result.pages:
        logger.info("[SmartOCR] No pages found, treating as scanned PDF")
        return True

    # Calculate total and average characters
    total_chars = 0
    total_garbage = 0

    for page in parse_result.pages:
        content = page.content or ""
        total_chars += len(content)

        # Count garbage characters (non-printable, excessive special chars)
        garbage_count = _count_garbage_chars(content)
        total_garbage += garbage_count

    page_count = len(parse_result.pages)
    avg_chars_per_page = total_chars / page_count if page_count > 0 else 0
    garbage_ratio = total_garbage / total_chars if total_chars > 0 else 0

    logger.info(
        f"[SmartOCR] Analysis: pages={page_count}, "
        f"avg_chars={avg_chars_per_page:.1f}, "
        f"garbage_ratio={garbage_ratio:.2%}"
    )

    # Check conditions for scanned PDF
    is_too_few_chars = avg_chars_per_page < min_chars_per_page
    is_too_much_garbage = garbage_ratio > max_garbage_ratio

    if is_too_few_chars:
        logger.info(
            f"[SmartOCR] Detected scanned PDF: avg chars ({avg_chars_per_page:.1f}) "
            f"< threshold ({min_chars_per_page})"
        )
        return True

    if is_too_much_garbage:
        logger.info(
            f"[SmartOCR] Detected scanned PDF: garbage ratio ({garbage_ratio:.2%}) "
            f"> threshold ({max_garbage_ratio:.2%})"
        )
        return True

    logger.info("[SmartOCR] PDF appears to be text-based, no OCR needed")
    return False


def _count_garbage_chars(text: str) -> int:
    """
    Count garbage/non-standard characters in text.

    Garbage characters include:
    - Non-printable characters (except newlines, tabs)
    - Excessive special Unicode characters
    - Common OCR artifacts

    Args:
        text: Text content to analyze.

    Returns:
        Count of garbage characters.
    """
    if not text:
        return 0

    garbage_count = 0

    # Pattern for common garbage: control characters, replacement chars, etc.
    # Exclude normal whitespace (space, tab, newline)
    garbage_pattern = re.compile(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f"  # Control characters
        r"\ufffd"  # Replacement character
        r"\u2028\u2029"  # Line/paragraph separators (unusual)
        r"]"
    )

    garbage_count += len(garbage_pattern.findall(text))

    # Check for excessive sequences of special characters (common OCR artifacts)
    # e.g., "###", "***", "___", "|||"
    artifact_pattern = re.compile(r"([^\w\s])\1{3,}")
    garbage_count += len(artifact_pattern.findall(text)) * 3

    # Check for excessive single special characters mixed with text
    # High ratio of punctuation/symbols to alphanumeric is suspicious
    alpha_count = len(re.findall(r"[a-zA-Z\u4e00-\u9fff]", text))
    special_count = len(re.findall(r"[^\w\s]", text))

    # If special chars > alpha chars, count excess as garbage
    if alpha_count > 0 and special_count > alpha_count * 2:
        garbage_count += special_count - alpha_count

    return garbage_count













