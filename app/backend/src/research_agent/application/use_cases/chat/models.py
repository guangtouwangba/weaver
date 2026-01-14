"""Data models for chat use case."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID
import re


@dataclass
class SourceRef:
    """Source reference."""

    document_id: UUID
    page_number: int
    snippet: str
    similarity: float


class StreamingRefInjector:
    def __init__(self, default_video_source_id: str | None):
        self.default_video_source_id = default_video_source_id
        self.buffer = ""

    _time_pattern = re.compile(r"\[(?:TIME:)?(\d{1,2}:\d{2}(?::\d{2})?)\]")

    def process_token(self, token: str) -> str:
        self.buffer += token
        safe_text, remaining = self._split_safe(self.buffer)
        self.buffer = remaining
        return self._transform(safe_text)

    def flush(self) -> str:
        out = self._transform(self.buffer)
        self.buffer = ""
        return out

    def _split_safe(self, text: str) -> tuple[str, str]:
        last_open = text.rfind("[")
        if last_open == -1:
            return text, ""

        last_close = text.rfind("]")
        if last_close < last_open:
            return text[:last_open], text[last_open:]

        return text, ""

    def _time_str_to_seconds(self, time_str: str) -> int:
        try:
            parts = list(map(int, time_str.split(":")))
            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
            return 0
        except ValueError:
            return 0

    def _transform(self, text: str) -> str:
        if not text:
            return ""

        def repl(match: re.Match[str]) -> str:
            ts = match.group(1)
            if not self.default_video_source_id:
                # If no video context is active, just return the timestamp text
                return ts

            seconds = self._time_str_to_seconds(ts)
            # Format: [MM:SS](video-source://<id>?t=<seconds>)
            return f"[{ts}](video-source://{self.default_video_source_id}?t={seconds})"

        return self._time_pattern.sub(repl, text)


@dataclass
class StreamEvent:
    """Streaming event."""

    type: str  # "token" | "sources" | "done" | "error" | "citations" | "status"
    content: str | None = None
    sources: list[SourceRef] | None = None
    citations: list[dict[str, Any]] | None = None  # Citations from long context mode
    step: str | None = (
        None  # For status events: rewriting, memory, analyzing, retrieving, ranking, generating
    )
    message: str | None = None  # Human-readable status message


@dataclass
class ContextRefs:
    """
    Context references persisted to ChatMessage.

    This information is saved to the database and used for:
    1. Displaying attached context sources when showing user messages in the frontend.
    2. Rebuilding entity state during history replay.
    """

    urls: list[dict[str, Any]] = field(default_factory=list)
    # Format: [{"id": "...", "title": "...", "platform": "...", "url": "..."}]

    node_ids: list[str] = field(default_factory=list)
    # List of Canvas node IDs

    nodes: list[dict[str, Any]] = field(default_factory=list)
    # Format: [{"id": "...", "title": "..."}]

    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Active entity mapping, format: {"entity_id": {"id": "...", "type": "video|document", "title": "..."}}

    focus: dict[str, Any] | None = None
    # Current focus entity

    def to_dict(self) -> dict[str, Any] | None:
        """Convert to JSON-serializable dict for DB storage."""
        result = {}
        if self.urls:
            result["urls"] = self.urls
        if self.node_ids:
            result["node_ids"] = self.node_ids
        if self.nodes:
            result["nodes"] = self.nodes
        if self.entities:
            result["entities"] = self.entities
        if self.focus:
            result["focus"] = self.focus
        return result if result else None

    def has_any_refs(self) -> bool:
        """Check if there are any context references."""
        return bool(self.urls or self.node_ids or self.nodes)


@dataclass
class ResolvedContext:
    """
    Complete context resolved by ContextEngine.

    Contains all context information needed to be passed to the RAG pipeline.
    """

    # === Text Context ===
    combined_context: str
    # Combined canvas + URL text content, passed directly to LLM

    # === Entity Tracking ===
    active_entities: dict[str, dict[str, Any]]
    # Active entities in the current session (reconstructed from history + current request)

    current_focus: dict[str, Any] | None
    # Current focus entity (recently attached resource)

    # === Persisted References ===
    context_refs_for_user_message: ContextRefs
    # References to be saved to the user message

    # === Video Processing ===
    default_video_source_id: str | None
    # Default video source ID for StreamingRefInjector

    # === Statistics (for trace) ===
    canvas_node_count: int = 0
    url_resource_count: int = 0


@dataclass
class StreamResult:
    """
    Result of streaming processing.

    Contains complete response information after all events are processed.
    """

    full_response: str
    # Complete AI response text

    sources: list[dict[str, Any]]
    # Format: [{"document_id": "...", "page_number": N, "snippet": "...", "similarity": 0.X}]

    retrieved_contexts: list[str]
    # List of retrieved original texts, used for evaluation

    token_count: int
    # Number of generated tokens

    active_entities: dict[str, dict[str, Any]]
    # Entity state updated during processing

    current_focus: dict[str, Any] | None
    # Focus updated during processing
