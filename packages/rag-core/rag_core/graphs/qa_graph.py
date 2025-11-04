"""LangGraph definition for question answering."""

from langgraph.graph import END, StateGraph

from rag_core.chains.vectorstore import retrieve_documents
from rag_core.chains.qa_chain import synthesize_answer
from rag_core.graphs.memory_nodes import (
    load_memory_node,
    retrieve_long_term_memory_node,
    contextualize_query_node,
    save_memory_node,
)
from shared_config.settings import AppSettings
from rag_core.graphs.callbacks import LoggingCallbackHandler
from rag_core.graphs.state import QueryState


def should_contextualize(state: QueryState) -> str:
    """Decide whether to contextualize the query based on chat history."""
    chat_history = state.chat_history
    if chat_history:
        return "contextualize"
    return "retrieve"


def retrieve_with_context(state: QueryState) -> dict:
    """
    Retrieve documents using the contextualized question if available.
    Falls back to original question if no contextualization.
    """
    # Use contextualized question if available, otherwise use original
    contextualized_question = state.contextualized_question
    if contextualized_question:
        print(f"🔍 [Retrieve] 使用重写后的问题进行检索: {contextualized_question}")
        # Temporarily update question for retrieval
        original_question = state.question
        # Create a modified state for retrieval
        state_dict = state.model_dump()
        state_dict["question"] = contextualized_question
        modified_state = QueryState(**state_dict)
        result_state = retrieve_documents(modified_state)
        
        # Convert result to dict and restore original question
        result_dict = result_state.model_dump() if hasattr(result_state, 'model_dump') else dict(result_state)
        result_dict["question"] = original_question
        return result_dict
    else:
        print(f"🔍 [Retrieve] 使用原始问题进行检索")
        result_state = retrieve_documents(state)
        # Convert to dict if it's a QueryState object
        return result_state.model_dump() if hasattr(result_state, 'model_dump') else dict(result_state)


def build_qa_graph(settings: AppSettings) -> StateGraph:
    """Create the QA graph DAG with layered conversational memory."""
    graph = StateGraph(QueryState)

    # Add nodes
    graph.add_node("load_memory", load_memory_node)  # Short-term memory
    graph.add_node("retrieve_long_term", retrieve_long_term_memory_node)  # Long-term memory
    graph.add_node("contextualize", contextualize_query_node)
    graph.add_node("retrieve", retrieve_with_context)
    graph.add_node("synthesize", synthesize_answer)
    graph.add_node("save_memory", save_memory_node)

    # Set entry point
    graph.set_entry_point("load_memory")
    
    # Always retrieve long-term memory after short-term
    graph.add_edge("load_memory", "retrieve_long_term")
    
    # Conditional edge: contextualize only if there's chat history
    graph.add_conditional_edges(
        "retrieve_long_term",
        should_contextualize,
        {
            "contextualize": "contextualize",
            "retrieve": "retrieve"
        }
    )
    
    # Flow from contextualize to retrieve
    graph.add_edge("contextualize", "retrieve")
    
    # Linear flow after retrieval
    graph.add_edge("retrieve", "synthesize")
    graph.add_edge("synthesize", "save_memory")
    graph.add_edge("save_memory", END)

    return graph.compile()


async def run_qa_graph(state: QueryState):
    """Execute the QA graph and return populated state."""
    settings = AppSettings()  # type: ignore[arg-type]
    graph = build_qa_graph(settings)
    # Pass callbacks in the config parameter of ainvoke
    return await graph.ainvoke(state, config={"callbacks": [LoggingCallbackHandler()]})
