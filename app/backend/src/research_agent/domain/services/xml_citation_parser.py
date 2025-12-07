"""XML citation parser service for Mega-Prompt RAG mode.

Parses XML-formatted <cite> tags from LLM output and extracts
document references and quoted text for source attribution.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple

from research_agent.shared.utils.logger import logger


@dataclass
class ParsedCitation:
    """Parsed citation from XML cite tag."""

    doc_id: str  # e.g., "doc_01"
    quote: str  # Verbatim text from document
    conclusion: str  # LLM's conclusion/statement
    start_pos: int  # Start position in original text
    end_pos: int  # End position in original text
    raw_tag: str  # Original XML tag string


class XMLCitationParser:
    """
    Parser for XML citation tags in LLM output.

    Supports parsing <cite doc_id="doc_XX" quote="...">conclusion</cite> tags
    with robust handling of edge cases and malformed tags.
    """

    # Primary pattern: strict format
    CITE_PATTERN = re.compile(
        r'<cite\s+doc_id="(doc_\d+)"\s+quote="([^"]+)">([^<]+)</cite>',
        re.DOTALL,
    )

    # Alternative pattern: handles attribute order variations
    CITE_PATTERN_ALT = re.compile(
        r'<cite\s+(?:doc_id="(doc_\d+)"\s+quote="([^"]+)"|quote="([^"]+)"\s+doc_id="(doc_\d+)")>([^<]+)</cite>',
        re.DOTALL,
    )

    # Pattern for detecting incomplete tags (for streaming)
    INCOMPLETE_TAG_PATTERN = re.compile(r"<cite[^>]*$", re.DOTALL)

    def parse(self, text: str) -> List[ParsedCitation]:
        """
        Parse all citation tags from text.

        Args:
            text: LLM output text containing <cite> tags

        Returns:
            List of ParsedCitation objects
        """
        citations = []

        # Try primary pattern first
        for match in self.CITE_PATTERN.finditer(text):
            doc_id = match.group(1)
            quote = match.group(2)
            conclusion = match.group(3).strip()

            citation = ParsedCitation(
                doc_id=doc_id,
                quote=self._unescape_xml(quote),
                conclusion=conclusion,
                start_pos=match.start(),
                end_pos=match.end(),
                raw_tag=match.group(0),
            )
            citations.append(citation)

        logger.debug(f"[XMLCitationParser] Parsed {len(citations)} citations from text")
        return citations

    def parse_streaming(self, buffer: str) -> Tuple[List[ParsedCitation], str, Optional[str]]:
        """
        Parse citations from streaming buffer.

        This method is designed for real-time parsing during LLM streaming.
        It returns completed citations and the remaining buffer.

        Args:
            buffer: Accumulated text buffer from streaming

        Returns:
            Tuple of:
            - List of completed citations
            - Remaining buffer (text after last complete citation or incomplete tag start)
            - Text to emit (text before any citations, safe to display)
        """
        citations = []
        text_to_emit = ""
        remaining_buffer = buffer

        # Find all complete citations
        last_end = 0
        for match in self.CITE_PATTERN.finditer(buffer):
            # Emit text before this citation
            if match.start() > last_end:
                text_to_emit += buffer[last_end : match.start()]

            citation = ParsedCitation(
                doc_id=match.group(1),
                quote=self._unescape_xml(match.group(2)),
                conclusion=match.group(3).strip(),
                start_pos=match.start(),
                end_pos=match.end(),
                raw_tag=match.group(0),
            )
            citations.append(citation)
            last_end = match.end()

        # Check for incomplete tag at the end
        remaining_text = buffer[last_end:]
        incomplete_match = self.INCOMPLETE_TAG_PATTERN.search(remaining_text)

        if incomplete_match:
            # There's an incomplete tag - keep it in buffer
            text_to_emit += remaining_text[: incomplete_match.start()]
            remaining_buffer = remaining_text[incomplete_match.start() :]
        else:
            # No incomplete tag - emit remaining text
            text_to_emit += remaining_text
            remaining_buffer = ""

        return citations, remaining_buffer, text_to_emit

    def extract_clean_text(self, text: str) -> str:
        """
        Extract clean text by removing citation tags but keeping conclusions.

        Args:
            text: Text with <cite> tags

        Returns:
            Clean text with citations replaced by their conclusions
        """
        # Replace <cite doc_id="..." quote="...">conclusion</cite> with just "conclusion"
        clean = self.CITE_PATTERN.sub(r"\3", text)
        return clean

    def get_citation_positions(self, text: str) -> List[Dict[str, Any]]:
        """
        Get positions of citations for rendering.

        Returns positions in the clean text (after tag removal) for
        frontend rendering.

        Args:
            text: Original text with <cite> tags

        Returns:
            List of dicts with position info for rendering
        """
        positions = []
        clean_text = ""
        current_clean_pos = 0

        last_end = 0
        for match in self.CITE_PATTERN.finditer(text):
            # Add text before this citation to clean text
            before_text = text[last_end : match.start()]
            clean_text += before_text
            current_clean_pos += len(before_text)

            # The citation's conclusion text
            conclusion = match.group(3).strip()
            conclusion_start = current_clean_pos
            conclusion_end = current_clean_pos + len(conclusion)

            positions.append(
                {
                    "doc_id": match.group(1),
                    "quote": self._unescape_xml(match.group(2)),
                    "conclusion": conclusion,
                    "clean_start": conclusion_start,
                    "clean_end": conclusion_end,
                }
            )

            clean_text += conclusion
            current_clean_pos += len(conclusion)
            last_end = match.end()

        # Add remaining text
        clean_text += text[last_end:]

        return positions

    def validate_citation(self, citation: ParsedCitation) -> Tuple[bool, List[str]]:
        """
        Validate a parsed citation.

        Args:
            citation: ParsedCitation to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check doc_id format
        if not re.match(r"^doc_\d{2}$", citation.doc_id):
            errors.append(f"Invalid doc_id format: {citation.doc_id}")

        # Check quote length (minimum 5 words or 20 characters)
        quote_words = len(citation.quote.split())
        if quote_words < 3 and len(citation.quote) < 20:
            errors.append(f"Quote too short: {quote_words} words, {len(citation.quote)} chars")

        # Check conclusion is not empty
        if not citation.conclusion.strip():
            errors.append("Empty conclusion")

        return len(errors) == 0, errors

    def _unescape_xml(self, text: str) -> str:
        """Unescape XML entities in text."""
        replacements = [
            ("&lt;", "<"),
            ("&gt;", ">"),
            ("&amp;", "&"),
            ("&quot;", '"'),
            ("&apos;", "'"),
        ]
        result = text
        for entity, char in replacements:
            result = result.replace(entity, char)
        return result


# Convenience functions


def parse_citations(text: str) -> List[ParsedCitation]:
    """Parse citations from text using default parser."""
    parser = XMLCitationParser()
    return parser.parse(text)


def extract_clean_text(text: str) -> str:
    """Extract clean text from text with citation tags."""
    parser = XMLCitationParser()
    return parser.extract_clean_text(text)


def parse_streaming_buffer(
    buffer: str,
) -> Tuple[List[ParsedCitation], str, Optional[str]]:
    """Parse citations from streaming buffer."""
    parser = XMLCitationParser()
    return parser.parse_streaming(buffer)
