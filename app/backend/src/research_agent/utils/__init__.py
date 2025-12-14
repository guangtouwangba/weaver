"""Utility modules for research agent."""

from research_agent.utils.text_locator import (
    LocationResult,
    TextLocator,
    calculate_page_number,
    locate_citation_in_document,
)

__all__ = [
    "TextLocator",
    "LocationResult",
    "locate_citation_in_document",
    "calculate_page_number",
]
