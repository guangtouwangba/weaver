"""LangGraph definition for question answering."""

from langgraph.graph import END, StateGraph

from rag_core.chains.vectorstore import retrieve_documents
from rag_core.chains.qa_chain import synthesize_answer
from shared_config.settings import AppSettings
from rag_core.graphs.callbacks import LoggingCallbackHandler
from rag_core.graphs.state import QueryState


def build_qa_graph(settings: AppSettings) -> StateGraph:
    """Create the QA graph DAG."""
    graph = StateGraph(QueryState)

    graph.add_node("retrieve", retrieve_documents)
    graph.add_node("synthesize", synthesize_answer)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


async def run_qa_graph(state: QueryState):
    """Execute the QA graph and return populated state."""
    settings = AppSettings()  # type: ignore[arg-type]
    graph = build_qa_graph(settings)
    # Pass callbacks in the config parameter of ainvoke
    return await graph.ainvoke(state, config={"callbacks": [LoggingCallbackHandler()]})
