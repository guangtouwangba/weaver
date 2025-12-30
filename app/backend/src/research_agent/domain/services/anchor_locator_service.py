"""
Anchor Locator Service for Source Anchor positioning.

MVP Strategy:
- PDF: page + char_start + char_end + context_hash (for validation)
- Web: url + text_quote + context_window (surrounding text)

This service provides:
1. Create anchor from PDF highlight/selection
2. Create anchor from web selection
3. Validate anchor (check if still locatable)
4. Get jump-back info (coordinates for returning to source)
"""

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from research_agent.domain.entities.thinking_path import (
    AnchorStatus,
    PDFLocator,
    SourceAnchor,
    WebLocator,
)
from research_agent.shared.utils.logger import logger
from research_agent.utils.text_locator import LocationResult, TextLocator


@dataclass
class AnchorJumpInfo:
    """Information needed to jump back to an anchor's source location."""

    anchor_id: str
    source_type: str  # "pdf", "web", "chat"
    source_id: Optional[str] = None  # Document ID for PDF
    source_url: Optional[str] = None  # URL for web
    page: Optional[int] = None  # Page number for PDF
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    quote_text: str = ""
    status: str = "valid"  # "valid", "stale", "broken"
    confidence: float = 100.0  # How confident we are in the location


@dataclass
class AnchorValidationResult:
    """Result of validating an anchor against current source content."""

    is_valid: bool
    status: AnchorStatus
    match_score: float = 0.0
    suggested_update: Optional[Dict[str, Any]] = None  # New locator if position changed
    message: str = ""


class AnchorLocatorService:
    """
    Service for creating and validating source anchors.

    MVP Implementation:
    - PDF anchors use page + character positions + context hash
    - Web anchors use URL + quote + context window
    - Validation uses fuzzy matching to handle minor changes
    """

    def __init__(self, fuzzy_threshold: int = 80):
        """
        Initialize the anchor locator service.

        Args:
            fuzzy_threshold: Minimum score (0-100) to consider an anchor still valid
        """
        self.text_locator = TextLocator(fuzzy_threshold=fuzzy_threshold)
        self.fuzzy_threshold = fuzzy_threshold

    # =========================================================================
    # PDF Anchor Creation
    # =========================================================================

    def create_pdf_anchor(
        self,
        project_id: UUID,
        document_id: UUID,
        quote_text: str,
        page: int,
        char_start: Optional[int] = None,
        char_end: Optional[int] = None,
        full_content: Optional[str] = None,
        context_window_size: int = 100,
    ) -> SourceAnchor:
        """
        Create a source anchor for a PDF selection.

        Args:
            project_id: Project ID
            document_id: Document ID
            quote_text: The selected text
            page: Page number (1-indexed)
            char_start: Character start position (optional)
            char_end: Character end position (optional)
            full_content: Full document content for generating context hash
            context_window_size: Size of context window for hash

        Returns:
            New SourceAnchor entity
        """
        # Generate context hash for validation
        context_hash = None
        if full_content and char_start is not None:
            context_hash = self._generate_context_hash(
                full_content, char_start, context_window_size
            )

        locator = PDFLocator(
            page=page,
            char_start=char_start,
            char_end=char_end,
            context_hash=context_hash,
        )

        return SourceAnchor(
            project_id=project_id,
            source_type="pdf",
            source_id=document_id,
            quote_text=quote_text,
            locator=locator.to_dict(),
            status=AnchorStatus.VALID,
        )

    def create_pdf_anchor_from_highlight(
        self,
        project_id: UUID,
        document_id: UUID,
        quote_text: str,
        page: int,
        start_offset: int,
        end_offset: int,
        full_content: Optional[str] = None,
    ) -> SourceAnchor:
        """
        Create anchor from existing highlight data.

        Args:
            project_id: Project ID
            document_id: Document ID
            quote_text: Highlighted text
            page: Page number
            start_offset: Start offset in page
            end_offset: End offset in page
            full_content: Full document content

        Returns:
            New SourceAnchor entity
        """
        return self.create_pdf_anchor(
            project_id=project_id,
            document_id=document_id,
            quote_text=quote_text,
            page=page,
            char_start=start_offset,
            char_end=end_offset,
            full_content=full_content,
        )

    # =========================================================================
    # Web Anchor Creation
    # =========================================================================

    def create_web_anchor(
        self,
        project_id: UUID,
        source_url: str,
        quote_text: str,
        selector: Optional[str] = None,
        context_window: Optional[str] = None,
    ) -> SourceAnchor:
        """
        Create a source anchor for a web page selection.

        Args:
            project_id: Project ID
            source_url: URL of the web page
            quote_text: The selected text
            selector: CSS selector or XPath to the element (optional)
            context_window: Surrounding text for validation (optional)

        Returns:
            New SourceAnchor entity
        """
        # If no context window provided, use the quote itself
        if not context_window:
            context_window = quote_text[:200] if len(quote_text) > 200 else quote_text

        locator = WebLocator(
            selector=selector,
            context_window=context_window,
        )

        return SourceAnchor(
            project_id=project_id,
            source_type="web",
            source_url=source_url,
            quote_text=quote_text,
            locator=locator.to_dict(),
            status=AnchorStatus.VALID,
        )

    # =========================================================================
    # Chat/Manual Anchor Creation
    # =========================================================================

    def create_chat_anchor(
        self,
        project_id: UUID,
        quote_text: str,
        chat_session_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> SourceAnchor:
        """
        Create a source anchor for a chat message reference.

        Args:
            project_id: Project ID
            quote_text: The referenced text
            chat_session_id: Chat session ID
            message_id: Specific message ID

        Returns:
            New SourceAnchor entity
        """
        locator = {
            "chat_session_id": chat_session_id,
            "message_id": message_id,
        }

        return SourceAnchor(
            project_id=project_id,
            source_type="chat",
            quote_text=quote_text,
            locator=locator,
            status=AnchorStatus.VALID,
        )

    def create_manual_anchor(
        self,
        project_id: UUID,
        quote_text: str,
        source_description: str = "",
    ) -> SourceAnchor:
        """
        Create a manual anchor without a specific source location.

        Args:
            project_id: Project ID
            quote_text: The text to anchor
            source_description: Human-readable description of source

        Returns:
            New SourceAnchor entity
        """
        locator = {
            "description": source_description,
        }

        return SourceAnchor(
            project_id=project_id,
            source_type="manual",
            quote_text=quote_text,
            locator=locator,
            status=AnchorStatus.VALID,
        )

    # =========================================================================
    # Anchor Validation
    # =========================================================================

    def validate_pdf_anchor(
        self,
        anchor: SourceAnchor,
        current_content: str,
        page_map: Optional[List[Dict[str, Any]]] = None,
    ) -> AnchorValidationResult:
        """
        Validate a PDF anchor against current document content.

        Args:
            anchor: The anchor to validate
            current_content: Current full document content
            page_map: Page boundaries for position mapping

        Returns:
            Validation result with status and suggestions
        """
        if anchor.source_type != "pdf":
            return AnchorValidationResult(
                is_valid=False,
                status=AnchorStatus.BROKEN,
                message="Not a PDF anchor",
            )

        # Try to locate the quote in current content
        result = self.text_locator.locate(current_content, anchor.quote_text, page_map)

        if result.found and result.match_score >= self.fuzzy_threshold:
            # Check if position changed significantly
            pdf_locator = anchor.get_pdf_locator()
            position_changed = False

            if pdf_locator and pdf_locator.char_start is not None:
                if result.char_start != pdf_locator.char_start:
                    position_changed = True

            if position_changed:
                # Anchor is valid but position changed - suggest update
                new_context_hash = self._generate_context_hash(
                    current_content, result.char_start, 100
                )
                return AnchorValidationResult(
                    is_valid=True,
                    status=AnchorStatus.STALE,
                    match_score=result.match_score,
                    suggested_update={
                        "char_start": result.char_start,
                        "char_end": result.char_end,
                        "page": result.page_number,
                        "context_hash": new_context_hash,
                    },
                    message="Position changed, update recommended",
                )
            else:
                return AnchorValidationResult(
                    is_valid=True,
                    status=AnchorStatus.VALID,
                    match_score=result.match_score,
                    message="Anchor is valid",
                )
        else:
            return AnchorValidationResult(
                is_valid=False,
                status=AnchorStatus.BROKEN,
                match_score=result.match_score if result else 0.0,
                message="Could not locate quote in current content",
            )

    def validate_web_anchor(
        self,
        anchor: SourceAnchor,
        current_page_content: str,
    ) -> AnchorValidationResult:
        """
        Validate a web anchor against current page content.

        Args:
            anchor: The anchor to validate
            current_page_content: Current page text content

        Returns:
            Validation result with status
        """
        if anchor.source_type != "web":
            return AnchorValidationResult(
                is_valid=False,
                status=AnchorStatus.BROKEN,
                message="Not a web anchor",
            )

        # Try to locate the quote
        result = self.text_locator.locate(current_page_content, anchor.quote_text)

        if result.found and result.match_score >= self.fuzzy_threshold:
            return AnchorValidationResult(
                is_valid=True,
                status=AnchorStatus.VALID,
                match_score=result.match_score,
                message="Anchor is valid",
            )
        else:
            return AnchorValidationResult(
                is_valid=False,
                status=AnchorStatus.BROKEN,
                match_score=result.match_score if result else 0.0,
                message="Could not locate quote in current content",
            )

    # =========================================================================
    # Jump Back Information
    # =========================================================================

    def get_jump_info(
        self,
        anchor: SourceAnchor,
        document_content: Optional[str] = None,
        page_map: Optional[List[Dict[str, Any]]] = None,
    ) -> AnchorJumpInfo:
        """
        Get jump-back information for navigating to anchor location.

        Args:
            anchor: The anchor to get jump info for
            document_content: Optional document content for re-locating
            page_map: Optional page boundaries

        Returns:
            Jump information for UI navigation
        """
        jump_info = AnchorJumpInfo(
            anchor_id=str(anchor.id),
            source_type=anchor.source_type,
            source_id=str(anchor.source_id) if anchor.source_id else None,
            source_url=anchor.source_url,
            quote_text=anchor.quote_text,
            status=anchor.status.value
            if isinstance(anchor.status, AnchorStatus)
            else anchor.status,
        )

        if anchor.source_type == "pdf":
            pdf_locator = anchor.get_pdf_locator()
            if pdf_locator:
                jump_info.page = pdf_locator.page
                jump_info.char_start = pdf_locator.char_start
                jump_info.char_end = pdf_locator.char_end

            # Re-locate if content provided and positions are missing
            if document_content and (jump_info.char_start is None):
                result = self.text_locator.locate(document_content, anchor.quote_text, page_map)
                if result.found:
                    jump_info.char_start = result.char_start
                    jump_info.char_end = result.char_end
                    jump_info.page = result.page_number or jump_info.page
                    jump_info.confidence = result.match_score

        return jump_info

    def get_jump_info_batch(
        self,
        anchors: List[SourceAnchor],
        document_contents: Optional[Dict[str, str]] = None,
    ) -> List[AnchorJumpInfo]:
        """
        Get jump info for multiple anchors.

        Args:
            anchors: List of anchors
            document_contents: Dict of document_id -> content

        Returns:
            List of jump information
        """
        results = []
        for anchor in anchors:
            content = None
            if document_contents and anchor.source_id:
                content = document_contents.get(str(anchor.source_id))
            results.append(self.get_jump_info(anchor, content))
        return results

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _generate_context_hash(
        self,
        content: str,
        position: int,
        window_size: int = 100,
    ) -> str:
        """
        Generate a hash of the context around a position.

        This helps detect if the surrounding content has changed,
        even if the exact quote is still present.
        """
        start = max(0, position - window_size)
        end = min(len(content), position + window_size)
        context = content[start:end]

        # Normalize whitespace for consistent hashing
        normalized = " ".join(context.split())

        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def update_anchor_from_validation(
        self,
        anchor: SourceAnchor,
        validation: AnchorValidationResult,
    ) -> SourceAnchor:
        """
        Update an anchor based on validation results.

        Args:
            anchor: The anchor to update
            validation: Validation result with suggestions

        Returns:
            Updated anchor
        """
        anchor.status = validation.status

        if validation.suggested_update and anchor.source_type == "pdf":
            # Update locator with new positions
            locator = anchor.locator.copy()
            locator.update(validation.suggested_update)
            anchor.locator = locator

        return anchor


# Convenience function for creating anchors from various sources
def create_anchor_from_selection(
    project_id: UUID,
    selection_type: str,
    quote_text: str,
    **kwargs,
) -> SourceAnchor:
    """
    Create an anchor from a selection.

    Args:
        project_id: Project ID
        selection_type: "pdf", "web", "chat", "manual"
        quote_text: Selected text
        **kwargs: Type-specific parameters

    Returns:
        New SourceAnchor
    """
    service = AnchorLocatorService()

    if selection_type == "pdf":
        return service.create_pdf_anchor(
            project_id=project_id,
            document_id=kwargs.get("document_id"),
            quote_text=quote_text,
            page=kwargs.get("page", 1),
            char_start=kwargs.get("char_start"),
            char_end=kwargs.get("char_end"),
            full_content=kwargs.get("full_content"),
        )
    elif selection_type == "web":
        return service.create_web_anchor(
            project_id=project_id,
            source_url=kwargs.get("source_url", ""),
            quote_text=quote_text,
            selector=kwargs.get("selector"),
            context_window=kwargs.get("context_window"),
        )
    elif selection_type == "chat":
        return service.create_chat_anchor(
            project_id=project_id,
            quote_text=quote_text,
            chat_session_id=kwargs.get("chat_session_id"),
            message_id=kwargs.get("message_id"),
        )
    else:
        return service.create_manual_anchor(
            project_id=project_id,
            quote_text=quote_text,
            source_description=kwargs.get("source_description", ""),
        )
















