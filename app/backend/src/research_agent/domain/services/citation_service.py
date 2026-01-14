"""Citation service for grounding references in long context mode."""

import json
import re
from dataclasses import dataclass
from uuid import UUID

from research_agent.shared.utils.logger import logger


@dataclass
class Citation:
    """Citation data structure."""

    document_id: UUID
    page_number: int
    char_start: int
    char_end: int
    paragraph_index: int | None = None
    sentence_index: int | None = None
    snippet: str = ""  # Quoted text snippet


@dataclass
class CitationMarker:
    """Citation marker parsed from LLM output."""

    text: str  # Associated text
    marker: str  # Original marker (e.g., [doc_id:page:start:end])
    citation: Citation  # Parsed citation object


class CitationService:
    """Service for generating and parsing citations."""

    # Regex pattern for inline citation markers: [doc_id:page:start:end]
    INLINE_CITATION_PATTERN = re.compile(
        r"\[([a-f0-9\-]{36}):(\d+):(\d+):(\d+)\]", re.IGNORECASE
    )

    def parse_citation_markers(self, text: str) -> list[CitationMarker]:
        """
        Parse citation markers from LLM output.

        Supports both inline format: [doc_id:page:start:end]
        and structured JSON format.

        Args:
            text: LLM output text with citation markers

        Returns:
            List of CitationMarker objects
        """
        markers = []

        # Parse inline citations
        for match in self.INLINE_CITATION_PATTERN.finditer(text):
            doc_id_str, page_str, start_str, end_str = match.groups()
            try:
                citation = Citation(
                    document_id=UUID(doc_id_str),
                    page_number=int(page_str),
                    char_start=int(start_str),
                    char_end=int(end_str),
                )
                marker = CitationMarker(
                    text=text[max(0, match.start() - 50) : match.end() + 50],
                    marker=match.group(0),
                    citation=citation,
                )
                markers.append(marker)
            except (ValueError, AttributeError) as e:
                logger.warning(f"[Citation] Failed to parse citation marker {match.group(0)}: {e}")

        # Try to parse structured JSON citations
        # Look for JSON objects with citation information
        json_pattern = re.compile(r'\{[^{}]*"citations"[^{}]*\}', re.IGNORECASE)
        for match in json_pattern.finditer(text):
            try:
                data = json.loads(match.group(0))
                if "citations" in data:
                    for cit_data in data["citations"]:
                        citation = Citation(
                            document_id=UUID(cit_data.get("document_id")),
                            page_number=int(cit_data.get("page_number", 0)),
                            char_start=int(cit_data.get("char_start", 0)),
                            char_end=int(cit_data.get("char_end", 0)),
                            paragraph_index=cit_data.get("paragraph_index"),
                            sentence_index=cit_data.get("sentence_index"),
                            snippet=cit_data.get("snippet", ""),
                        )
                        marker = CitationMarker(
                            text=data.get("text", ""),
                            marker=match.group(0),
                            citation=citation,
                        )
                        markers.append(marker)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"[Citation] Failed to parse JSON citation: {e}")

        logger.info(f"[Citation] Parsed {len(markers)} citation markers from text")
        return markers

    def format_citation(self, citation: Citation, format_type: str = "inline") -> str:
        """
        Format citation as string.

        Args:
            citation: Citation object
            format_type: "inline" or "structured"

        Returns:
            Formatted citation string
        """
        if format_type == "inline":
            return f"[{citation.document_id}:{citation.page_number}:{citation.char_start}:{citation.char_end}]"
        elif format_type == "structured":
            return json.dumps(
                {
                    "document_id": str(citation.document_id),
                    "page_number": citation.page_number,
                    "char_start": citation.char_start,
                    "char_end": citation.char_end,
                    "paragraph_index": citation.paragraph_index,
                    "sentence_index": citation.sentence_index,
                    "snippet": citation.snippet,
                },
                ensure_ascii=False,
            )
        else:
            return str(citation)

    async def validate_citation(
        self, citation: Citation, document_id: UUID, max_char: int | None = None
    ) -> bool:
        """
        Validate citation against document.

        Args:
            citation: Citation to validate
            document_id: Expected document ID
            max_char: Maximum character position in document (optional)

        Returns:
            True if citation is valid
        """
        # Check document ID matches
        if citation.document_id != document_id:
            logger.warning(
                f"[Citation] Document ID mismatch: {citation.document_id} != {document_id}"
            )
            return False

        # Check character positions are valid
        if citation.char_start < 0 or citation.char_end < citation.char_start:
            logger.warning(
                f"[Citation] Invalid character positions: start={citation.char_start}, "
                f"end={citation.char_end}"
            )
            return False

        # Check against max character if provided
        if max_char and citation.char_end > max_char:
            logger.warning(
                f"[Citation] Character end exceeds document length: {citation.char_end} > {max_char}"
            )
            return False

        return True

    def generate_citation_metadata(
        self, content: str, document_id: UUID, page_number: int = 0
    ) -> list[Citation]:
        """
        Generate citation metadata for content.

        This is a helper method that can be used to pre-generate citations
        during document processing.

        Args:
            content: Document content
            document_id: Document ID
            page_number: Page number

        Returns:
            List of Citation objects
        """
        citations = []
        char_pos = 0

        # Simple sentence-based citation generation
        sentences = re.split(r"[.!?]\s+", content)
        for sentence_idx, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            start_pos = char_pos
            end_pos = char_pos + len(sentence)

            citation = Citation(
                document_id=document_id,
                page_number=page_number,
                char_start=start_pos,
                char_end=end_pos,
                sentence_index=sentence_idx,
                snippet=sentence[:100] + "..." if len(sentence) > 100 else sentence,
            )
            citations.append(citation)

            char_pos = end_pos + 2  # Account for sentence separator

        return citations


