
import sys
from typing import Any, Dict, Optional

# --- EMBEDDED CLASS FOR VERIFICATION ---
class ConversationContext:
    """
    Manages conversation context and resolves entity references.
    
    Tracks entities (videos, documents) mentioned in the conversation and 
    resolves natural language references like "this video" or "that pdf" 
    to specific entity IDs.
    """
    
    def __init__(self, entities: Dict[str, Any] | None = None, focus: Dict[str, Any] | None = None):
        self.entities = entities or {}
        self.current_focus = focus
        
    def resolve_reference(self, query: str) -> Dict[str, Any] | None:
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
        
    def _find_last_entity_by_type(self, entity_type: str) -> Dict[str, Any] | None:
        """Find the most recently engaged entity of a specific type."""
        # Sort entities by timestamp (assuming metadata has it, or we rely on insertion order)
        matches = [
            e for e in self.entities.values() 
            if e.get("type") == entity_type
        ]
        return matches[-1] if matches else None
        
    def _get_most_recent_entity(self) -> Dict[str, Any] | None:
        """Get the absolute most recent entity."""
        if not self.entities:
            return None
        return list(self.entities.values())[-1]

# --- TESTS ---

def test_resolve_reference_video():
    print("Testing resolve_reference_video...")
    entities = {
        "v1": {"id": "v1", "type": "video", "title": "Intro to AI"},
        "v2": {"id": "v2", "type": "video", "title": "Advanced AI"},
    }
    ctx = ConversationContext(entities=entities)
    
    # "this video" should resolve to v2 (last added)
    resolved = ctx.resolve_reference("summarize this video")
    if resolved is None:
        raise AssertionError("Failed to resolve 'this video'")
    if resolved["id"] != "v2":
        raise AssertionError(f"Expected v2, got {resolved['id']}")
    print("PASS")
    
def test_resolve_reference_pdf():
    print("Testing resolve_reference_pdf...")
    entities = {
        "doc1": {"id": "doc1", "type": "document", "title": "Spec.pdf"},
        "v1": {"id": "v1", "type": "video", "title": "Video.mp4"},
    }
    ctx = ConversationContext(entities=entities)
    
    # "the pdf" should resolve to doc1, skipping v1
    resolved = ctx.resolve_reference("what is inside the pdf")
    if resolved is None:
        raise AssertionError("Failed to resolve 'the pdf'")
    if resolved["id"] != "doc1":
        raise AssertionError(f"Expected doc1, got {resolved['id']}")
    print("PASS")
    
def test_resolve_generic_focus():
    print("Testing resolve_generic_focus...")
    entities = {"v1": {"id": "v1", "type": "video", "title": "V1"}}
    ctx = ConversationContext(entities=entities, focus=entities["v1"])
    
    resolved = ctx.resolve_reference("tell me about it")
    if resolved is None:
        raise AssertionError("Failed to resolve generic 'it'")
    if resolved["id"] != "v1":
        raise AssertionError(f"Expected v1, got {resolved['id']}")
    print("PASS")

def main():
    try:
        test_resolve_reference_video()
        test_resolve_reference_pdf()
        test_resolve_generic_focus()
        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
