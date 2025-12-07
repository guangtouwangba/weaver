"""LangGraph workflow definitions."""

# V1: Original procedural implementation (for backward compatibility)
from research_agent.application.graphs.rag_graph import (
    GraphState,
    create_rag_graph,
    stream_rag_response,
)

# V2: Strategy-based implementation
from research_agent.application.graphs.rag_graph_v2 import (
    RAGGraphDependencies,
    RAGGraphState,
    create_default_rag_graph,
    create_rag_graph_v2,
    stream_rag_response_v2,
)

__all__ = [
    # V1 (backward compatible)
    "create_rag_graph",
    "stream_rag_response",
    "GraphState",
    # V2 (new strategy-based)
    "create_rag_graph_v2",
    "create_default_rag_graph",
    "stream_rag_response_v2",
    "RAGGraphState",
    "RAGGraphDependencies",
]
