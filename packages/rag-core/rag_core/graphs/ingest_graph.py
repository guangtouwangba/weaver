"""LangGraph definition for document ingestion."""

from langgraph.graph import END, StateGraph

from rag_core.chains.loaders import load_document
from rag_core.chains.splitters import split_document
from rag_core.chains.embeddings import embed_chunks
from rag_core.chains.vectorstore import persist_embeddings
from shared_config.settings import AppSettings
from rag_core.graphs.callbacks import LoggingCallbackHandler
from rag_core.graphs.state import DocumentIngestState


def build_ingest_graph(settings: AppSettings) -> StateGraph:
    """Create the ingestion graph DAG."""
    graph = StateGraph(DocumentIngestState)

    graph.add_node("load", load_document)
    graph.add_node("split", split_document)
    graph.add_node("embed", embed_chunks)
    graph.add_node("persist", persist_embeddings)

    graph.set_entry_point("load")
    graph.add_edge("load", "split")
    graph.add_edge("split", "embed")
    graph.add_edge("embed", "persist")
    graph.add_edge("persist", END)

    return graph.compile()


async def run_ingest_graph(state: DocumentIngestState) -> None:
    """Execute the ingest graph end to end."""
    settings = AppSettings()  # type: ignore[arg-type]
    graph = build_ingest_graph(settings)
    # Pass callbacks in the config parameter of ainvoke
    await graph.ainvoke(state, config={"callbacks": [LoggingCallbackHandler()]})
