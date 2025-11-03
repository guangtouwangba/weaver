"""Wrappers that expose graph builders used throughout the service."""

# Avoid circular imports by using lazy imports
# Import these directly from their modules instead of from this package

__all__ = ["build_ingest_graph", "build_qa_graph"]


def __getattr__(name: str):
    """Lazy import to avoid circular dependencies."""
    if name == "build_ingest_graph":
        from .ingest_graph import build_ingest_graph
        return build_ingest_graph
    elif name == "build_qa_graph":
        from .qa_graph import build_qa_graph
        return build_qa_graph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
