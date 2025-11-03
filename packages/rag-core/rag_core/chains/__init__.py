"""Composable LangChain building blocks used by LangGraph nodes."""

# Avoid circular imports by using lazy imports
# Import these directly from their modules instead of from this package

__all__ = [
    "build_embedding_function",
    "build_answer_chain",
    "build_text_splitter",
    "build_vector_store",
    "load_document_content",
]


def __getattr__(name: str):
    """Lazy import to avoid circular dependencies."""
    if name == "build_embedding_function":
        from .embeddings import build_embedding_function
        return build_embedding_function
    elif name == "build_answer_chain":
        from .qa_chain import build_answer_chain
        return build_answer_chain
    elif name == "build_text_splitter":
        from .splitters import build_text_splitter
        return build_text_splitter
    elif name == "build_vector_store":
        from .vectorstore import build_vector_store
        return build_vector_store
    elif name == "load_document_content":
        from .loaders import load_document_content
        return load_document_content
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
