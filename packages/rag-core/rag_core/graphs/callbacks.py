"""Reusable LangChain callback handlers for instrumentation."""

from typing import Any, Dict

from langchain.callbacks.base import BaseCallbackHandler


class LoggingCallbackHandler(BaseCallbackHandler):
    """Print simple lifecycle events to stdout for debugging."""

    def on_chain_end(self, outputs: Any, **kwargs: Any) -> None:
        """Log chain completion with sanitized outputs (hide large embeddings)."""
        try:
            sanitized = self._sanitize_outputs(outputs)
            print("[graph] chain finished", sanitized)
        except Exception as e:
            # Fallback: just print the type if sanitization fails
            print(f"[graph] chain finished (type: {type(outputs).__name__})")

    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Log chain errors."""
        print("[graph] chain error", repr(error))
    
    @staticmethod
    def _sanitize_outputs(outputs: Any) -> Dict[str, Any]:
        """Remove or summarize large data structures like embeddings."""
        # Convert Pydantic models to dict
        if hasattr(outputs, "model_dump"):
            # Pydantic v2
            outputs_dict = outputs.model_dump()
        elif hasattr(outputs, "dict"):
            # Pydantic v1 or other dict-like objects
            outputs_dict = outputs.dict()
        elif isinstance(outputs, dict):
            outputs_dict = outputs
        else:
            # Unknown type, return string representation
            return {"result": str(type(outputs).__name__)}
        
        sanitized = {}
        for key, value in outputs_dict.items():
            if key == "embeddings" and isinstance(value, list):
                # Summarize embeddings instead of printing all values
                sanitized[key] = f"<{len(value)} embeddings, dim={len(value[0]) if value else 0}>"
            elif key == "chunks" and isinstance(value, list):
                # Summarize chunks
                sanitized[key] = f"<{len(value)} chunks>"
            elif key == "documents" and isinstance(value, list):
                # Summarize documents
                sanitized[key] = f"<{len(value)} documents>"
            elif isinstance(value, str) and len(value) > 200:
                # Truncate long strings
                sanitized[key] = f"{value[:200]}... ({len(value)} chars total)"
            else:
                sanitized[key] = value
        return sanitized
