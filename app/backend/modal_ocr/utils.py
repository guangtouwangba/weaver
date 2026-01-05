"""Utility functions for Modal OCR service.

This module provides helper functions for PDF processing,
result merging, and page range calculations.
"""

from typing import List, Optional, Tuple


def calculate_page_ranges(
    total_pages: int,
    pages_per_chunk: int = 50,
) -> List[Tuple[int, int]]:
    """Calculate page ranges for parallel processing.

    Args:
        total_pages: Total number of pages in the document.
        pages_per_chunk: Maximum pages per chunk.

    Returns:
        List of (start_page, end_page) tuples (1-indexed, inclusive).

    Example:
        >>> calculate_page_ranges(125, 50)
        [(1, 50), (51, 100), (101, 125)]
    """
    if total_pages <= 0:
        return []

    ranges = []
    for start in range(1, total_pages + 1, pages_per_chunk):
        end = min(start + pages_per_chunk - 1, total_pages)
        ranges.append((start, end))

    return ranges


def merge_markdown_results(
    results: List[dict],
    page_separator: str = "\n\n---\n\n",
) -> str:
    """Merge multiple parsing results into a single markdown document.

    Args:
        results: List of parsing result dicts with 'content' and page info.
        page_separator: Separator to use between chunks.

    Returns:
        Merged markdown content.
    """
    # Sort by start page to ensure correct order
    sorted_results = sorted(results, key=lambda r: r.get("start_page", 0))

    # Filter out empty content and merge
    contents = [r["content"] for r in sorted_results if r.get("content")]

    return page_separator.join(contents)


def estimate_processing_time(
    page_count: int,
    pages_per_chunk: int = 50,
    seconds_per_page: float = 2.0,
    parallel: bool = True,
) -> dict:
    """Estimate processing time for a document.

    Args:
        page_count: Total number of pages.
        pages_per_chunk: Pages per parallel worker.
        seconds_per_page: Estimated seconds per page.
        parallel: Whether parallel processing will be used.

    Returns:
        Dict with time estimates and strategy info.
    """
    total_sequential_time = page_count * seconds_per_page

    if page_count <= pages_per_chunk or not parallel:
        return {
            "strategy": "single",
            "estimated_seconds": total_sequential_time,
            "num_workers": 1,
            "speedup": 1.0,
        }

    # Parallel processing
    num_chunks = (page_count + pages_per_chunk - 1) // pages_per_chunk
    # Account for parallel overhead (~10% overhead per chunk)
    parallel_overhead = 1.1
    parallel_time = (pages_per_chunk * seconds_per_page) * parallel_overhead

    return {
        "strategy": "parallel",
        "estimated_seconds": parallel_time,
        "num_workers": num_chunks,
        "speedup": total_sequential_time / parallel_time,
    }


def estimate_cost(
    page_count: int,
    pages_per_chunk: int = 50,
    gpu_cost_per_second: float = 0.00081,  # L40S pricing
    seconds_per_page: float = 2.0,
) -> dict:
    """Estimate Modal GPU cost for processing a document.

    Args:
        page_count: Total number of pages.
        pages_per_chunk: Pages per parallel worker.
        gpu_cost_per_second: Cost per second of GPU time.
        seconds_per_page: Estimated seconds per page.

    Returns:
        Dict with cost estimates.
    """
    if page_count <= pages_per_chunk:
        # Single task
        gpu_seconds = page_count * seconds_per_page
        return {
            "strategy": "single",
            "gpu_seconds": gpu_seconds,
            "estimated_cost_usd": gpu_seconds * gpu_cost_per_second,
        }

    # Parallel processing - each chunk runs on its own GPU
    num_chunks = (page_count + pages_per_chunk - 1) // pages_per_chunk
    # Each chunk processes up to pages_per_chunk pages
    max_chunk_pages = pages_per_chunk
    gpu_seconds_per_chunk = max_chunk_pages * seconds_per_page
    total_gpu_seconds = num_chunks * gpu_seconds_per_chunk

    return {
        "strategy": "parallel",
        "num_chunks": num_chunks,
        "gpu_seconds": total_gpu_seconds,
        "estimated_cost_usd": total_gpu_seconds * gpu_cost_per_second,
    }


def validate_pdf_bytes(document: bytes) -> Tuple[bool, Optional[str]]:
    """Validate that the given bytes represent a valid PDF.

    Args:
        document: Document content as bytes.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check PDF magic bytes
    if not document.startswith(b"%PDF"):
        return False, "Document does not appear to be a PDF (missing %PDF header)"

    if len(document) < 100:
        return False, "Document is too small to be a valid PDF"

    # Check for EOF marker (should be near the end)
    tail = document[-1024:] if len(document) > 1024 else document
    if b"%%EOF" not in tail:
        return False, "Document may be truncated (missing %%EOF marker)"

    return True, None
















