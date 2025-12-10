"""Document parser infrastructure module."""

from research_agent.infrastructure.parser.base import (
    DocumentParser,
    DocumentParsingError,
    DocumentType,
    ParsedPage,
    ParseResult,
)
from research_agent.infrastructure.parser.docling_parser import DoclingParser
from research_agent.infrastructure.parser.factory import ParserFactory

__all__ = [
    "DocumentParser",
    "DocumentParsingError",
    "DocumentType",
    "DoclingParser",
    "ParsedPage",
    "ParseResult",
    "ParserFactory",
]
