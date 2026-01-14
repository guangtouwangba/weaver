from typing import Any


class ConversationContext:
    """
    Manages conversation context and resolves entity references.

    Tracks entities (videos, documents) mentioned in the conversation and
    resolves natural language references like "this video" or "that pdf"
    to specific entity IDs.
    """

    def __init__(self, entities: dict[str, Any] | None = None, focus: dict[str, Any] | None = None):
        self.entities = entities or {}
        self.current_focus = focus

    def resolve_reference(self, query: str) -> dict[str, Any] | None:
        """
        Resolve a reference in the query to a specific entity.

        Strategies:
        1. Explicit Type: "this video" -> look for last accessed video
        2. Explicit Type: "the pdf" -> look for last accessed pdf
        3. Generic: "it", "this" -> use current focus if available
        """
        query_lower = query.lower()

        # Strategy 1: Explicit Video reference
        if "video" in query_lower or "part" in query_lower:
            return self._find_last_entity_by_type("video")

        # Strategy 2: Explicit Document/PDF reference
        if "pdf" in query_lower or "document" in query_lower or "doc" in query_lower:
            return self._find_last_entity_by_type("document")

        # Strategy 3: Generic reference (check focus first)
        generic_refs = ["this", "that", "it", "summary", "summarize"]
        if any(ref in query_lower for ref in generic_refs):
            if self.current_focus:
                return self.current_focus
            # If no focus, fallback to most recent entity
            return self._get_most_recent_entity()

        return None

    def _find_last_entity_by_type(self, entity_type: str) -> dict[str, Any] | None:
        """Find the most recently engaged entity of a specific type."""
        # Sort entities by timestamp (assuming metadata has it, or we rely on insertion order)
        matches = [
            e for e in self.entities.values()
            if e.get("type") == entity_type
        ]
        return matches[-1] if matches else None

    def _get_most_recent_entity(self) -> dict[str, Any] | None:
        """Get the absolute most recent entity."""
        if not self.entities:
            return None
        return list(self.entities.values())[-1]
