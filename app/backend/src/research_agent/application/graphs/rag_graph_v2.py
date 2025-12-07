"""
RAG Graph V2 - Strategy-based Implementation.

This is the refactored RAG workflow using the Strategy pattern.
The graph becomes a coordinator, delegating actual work to strategies.

Key improvements over rag_graph.py:
1. Decoupled from global settings - uses RAGConfig passed in state
2. Strategy pattern for retrieval/generation - easy to add HyDE, GraphRAG, etc.
3. Cleaner separation of concerns
4. Better testability via dependency injection
"""

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, List, Optional, TypedDict
from uuid import UUID

from langchain_core.documents import Document
from langgraph.graph import END, StateGraph

from research_agent.domain.entities.config import (
    IntentType,
    RAGConfig,
    RAGMode,
    RetrievalConfig,
    RetrievalStrategyType,
)
from research_agent.domain.services.config_service import get_config_service
from research_agent.domain.services.strategy_factory import StrategyFactory
from research_agent.domain.strategies.base import (
    GenerationResult,
    IGenerationStrategy,
    IRetrievalStrategy,
    RetrievalResult,
)
from research_agent.shared.utils.logger import logger

# -----------------------------------------------------------------------------
# Graph State
# -----------------------------------------------------------------------------


class RAGGraphState(TypedDict):
    """
    State for the RAG graph V2.

    Key difference from V1: includes config object that flows through the pipeline.
    """

    # Input
    question: str
    chat_history: List[tuple[str, str]]
    project_id: str  # UUID as string for serialization

    # Configuration (injected at start, flows through pipeline)
    config: dict  # RAGConfig serialized to dict

    # Query transformation
    rewritten_question: str

    # Intent classification
    intent_type: str
    intent_confidence: float

    # Retrieval
    retrieval_result: dict  # RetrievalResult serialized
    documents: List[Document]

    # Generation
    generation_result: dict  # GenerationResult serialized
    generation: str
    citations: List[dict]

    # Metadata
    rag_mode: str


# -----------------------------------------------------------------------------
# Graph Dependencies
# -----------------------------------------------------------------------------


@dataclass
class RAGGraphDependencies:
    """
    Dependencies required by the RAG graph.

    Injected at graph creation time, avoiding global state access.
    """

    retrieval_strategy: IRetrievalStrategy
    generation_strategy: IGenerationStrategy

    # Optional alternative strategies
    hybrid_retrieval_strategy: Optional[IRetrievalStrategy] = None
    long_context_generation_strategy: Optional[IGenerationStrategy] = None


# -----------------------------------------------------------------------------
# Node Functions
# -----------------------------------------------------------------------------


async def initialize_config(
    state: RAGGraphState,
    project_id: Optional[UUID] = None,
) -> RAGGraphState:
    """
    Initialize configuration for the RAG pipeline.

    If config is not provided in state, loads from ConfigurationService.
    """
    if state.get("config"):
        logger.debug("[RAG V2] Using provided config")
        return {}

    # Load config from service
    config_service = get_config_service()

    # Parse project_id
    pid = None
    if project_id:
        pid = project_id
    elif state.get("project_id"):
        pid = UUID(state["project_id"])

    config = config_service.get_config(project_id=pid)

    logger.info(
        f"[RAG V2] Initialized config: mode={config.mode}, retrieval={config.retrieval.strategy_type}"
    )

    return {
        "config": config.model_dump(),
        "rag_mode": config.mode.value,
    }


async def transform_query(
    state: RAGGraphState,
    deps: RAGGraphDependencies,
) -> RAGGraphState:
    """
    Transform/rewrite the query using chat history.

    Simplified version - full implementation would use IQueryTransformStrategy.
    """
    question = state["question"]
    chat_history = state.get("chat_history", [])

    # If no history, use original question
    if not chat_history:
        logger.info("[RAG V2] No chat history, using original question")
        return {"rewritten_question": question}

    # TODO: Implement query rewrite using IQueryTransformStrategy
    # For now, just use original question
    logger.info("[RAG V2] Query transformation (placeholder)")
    return {"rewritten_question": question}


async def classify_intent(
    state: RAGGraphState,
    deps: RAGGraphDependencies,
) -> RAGGraphState:
    """
    Classify the intent of the query.

    Simplified version - full implementation would use IIntentClassificationStrategy.
    """
    config_dict = state.get("config", {})
    intent_config = config_dict.get("intent_classification", {})

    if not intent_config.get("enabled", True):
        logger.info("[RAG V2] Intent classification disabled")
        return {
            "intent_type": IntentType.FACTUAL.value,
            "intent_confidence": 1.0,
        }

    # TODO: Implement using IIntentClassificationStrategy
    # For now, default to FACTUAL
    logger.info("[RAG V2] Intent classification (placeholder) -> FACTUAL")
    return {
        "intent_type": IntentType.FACTUAL.value,
        "intent_confidence": 0.8,
    }


async def retrieve_documents(
    state: RAGGraphState,
    deps: RAGGraphDependencies,
) -> RAGGraphState:
    """
    Retrieve documents using the configured strategy.

    Selects between vector, hybrid, or other strategies based on config.
    """
    query = state.get("rewritten_question", state["question"])
    project_id = UUID(state["project_id"])
    config_dict = state.get("config", {})

    # Reconstruct RetrievalConfig from dict
    retrieval_dict = config_dict.get("retrieval", {})
    retrieval_config = RetrievalConfig(**retrieval_dict)

    # Select strategy based on config
    strategy = deps.retrieval_strategy
    if retrieval_config.use_hybrid_search and deps.hybrid_retrieval_strategy:
        strategy = deps.hybrid_retrieval_strategy
        logger.info("[RAG V2] Using hybrid retrieval strategy")
    else:
        logger.info(f"[RAG V2] Using {strategy.name} retrieval strategy")

    # Execute retrieval
    result = await strategy.retrieve(
        query=query,
        project_id=project_id,
        config=retrieval_config,
    )

    logger.info(f"[RAG V2] Retrieved {result.document_count} documents")

    return {
        "retrieval_result": {
            "document_count": result.document_count,
            "strategy_name": result.strategy_name,
            "metadata": result.metadata,
        },
        "documents": result.documents,
    }


async def generate_response(
    state: RAGGraphState,
    deps: RAGGraphDependencies,
) -> RAGGraphState:
    """
    Generate response using the configured strategy.
    """
    question = state["question"]
    documents = state.get("documents", [])
    config_dict = state.get("config", {})
    rag_mode = state.get("rag_mode", "traditional")

    if not documents:
        logger.warning("[RAG V2] No documents for generation")
        return {
            "generation": "I don't have enough relevant information to answer this question.",
            "citations": [],
        }

    # Build context from documents
    context = "\n\n".join([doc.page_content for doc in documents])

    # Reconstruct configs from dicts
    from research_agent.domain.entities.config import GenerationConfig, LLMConfig

    generation_config = GenerationConfig(**config_dict.get("generation", {}))
    llm_config = LLMConfig(**config_dict.get("llm", {}))

    # Select strategy
    strategy = deps.generation_strategy
    if rag_mode == RAGMode.LONG_CONTEXT.value and deps.long_context_generation_strategy:
        strategy = deps.long_context_generation_strategy
        logger.info("[RAG V2] Using long context generation strategy")
    else:
        logger.info(f"[RAG V2] Using {strategy.name} generation strategy")

    # Execute generation
    result = await strategy.generate(
        query=question,
        context=context,
        config=generation_config,
        llm_config=llm_config,
    )

    logger.info(
        f"[RAG V2] Generated response: {len(result.content)} chars, {len(result.citations)} citations"
    )

    return {
        "generation_result": {
            "strategy_name": result.strategy_name,
            "metadata": result.metadata,
        },
        "generation": result.content,
        "citations": result.citations,
    }


# -----------------------------------------------------------------------------
# Graph Builder
# -----------------------------------------------------------------------------


def create_rag_graph_v2(
    deps: RAGGraphDependencies,
    use_intent_classification: bool = True,
    use_query_transform: bool = True,
) -> StateGraph:
    """
    Create the RAG graph V2 with strategy-based implementation.

    Args:
        deps: Injected dependencies (strategies)
        use_intent_classification: Enable intent classification node
        use_query_transform: Enable query transformation node

    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(RAGGraphState)

    # Add nodes with injected dependencies
    workflow.add_node("initialize", lambda s: initialize_config(s))

    if use_query_transform:
        workflow.add_node("transform_query", lambda s: transform_query(s, deps))

    if use_intent_classification:
        workflow.add_node("classify_intent", lambda s: classify_intent(s, deps))

    workflow.add_node("retrieve", lambda s: retrieve_documents(s, deps))
    workflow.add_node("generate", lambda s: generate_response(s, deps))

    # Build edges
    workflow.set_entry_point("initialize")

    if use_query_transform:
        workflow.add_edge("initialize", "transform_query")
        if use_intent_classification:
            workflow.add_edge("transform_query", "classify_intent")
            workflow.add_edge("classify_intent", "retrieve")
        else:
            workflow.add_edge("transform_query", "retrieve")
    else:
        if use_intent_classification:
            workflow.add_edge("initialize", "classify_intent")
            workflow.add_edge("classify_intent", "retrieve")
        else:
            workflow.add_edge("initialize", "retrieve")

    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


# -----------------------------------------------------------------------------
# Streaming Support
# -----------------------------------------------------------------------------


async def stream_rag_response_v2(
    question: str,
    project_id: UUID,
    deps: RAGGraphDependencies,
    chat_history: Optional[List[tuple[str, str]]] = None,
    config: Optional[RAGConfig] = None,
) -> AsyncIterator[dict[str, Any]]:
    """
    Stream RAG response using V2 strategy-based implementation.

    Args:
        question: User question
        project_id: Project UUID
        deps: Injected dependencies
        chat_history: Optional conversation history
        config: Optional pre-built configuration

    Yields:
        Event dicts: {"type": "sources"|"token"|"citations"|"done", ...}
    """
    logger.info(f"[RAG V2 Stream] Starting for: {question[:50]}...")

    # Initialize configuration
    if config is None:
        config_service = get_config_service()
        config = config_service.get_config(project_id=project_id)

    # Step 1: Retrieve documents
    retrieval_config = config.retrieval

    strategy = deps.retrieval_strategy
    if retrieval_config.use_hybrid_search and deps.hybrid_retrieval_strategy:
        strategy = deps.hybrid_retrieval_strategy

    retrieval_result = await strategy.retrieve(
        query=question,
        project_id=project_id,
        config=retrieval_config,
    )

    # Yield sources
    yield {
        "type": "sources",
        "documents": retrieval_result.documents,
    }

    if retrieval_result.is_empty:
        yield {
            "type": "token",
            "content": "I don't have enough relevant information to answer this question.",
        }
        yield {"type": "done"}
        return

    # Step 2: Stream generation
    context = "\n\n".join([doc.page_content for doc in retrieval_result.documents])

    strategy = deps.generation_strategy
    if config.mode == RAGMode.LONG_CONTEXT and deps.long_context_generation_strategy:
        strategy = deps.long_context_generation_strategy

    # Stream tokens
    full_response = ""
    async for token in strategy.stream(
        query=question,
        context=context,
        config=config.generation,
        llm_config=config.llm,
    ):
        full_response += token
        yield {"type": "token", "content": token}

    # Parse citations from full response
    if isinstance(strategy, type) and hasattr(strategy, "_parse_citations"):
        citations = strategy._parse_citations(full_response)
        if citations:
            yield {"type": "citations", "citations": citations}

    yield {"type": "done"}
    logger.info(f"[RAG V2 Stream] Complete: {len(full_response)} chars")


# -----------------------------------------------------------------------------
# Factory Functions
# -----------------------------------------------------------------------------


def create_default_rag_graph(
    embedding_service: Any,
    vector_store: Any,
    llm: Optional[Any] = None,
) -> StateGraph:
    """
    Create a RAG graph with default strategies.

    Convenience factory for common use case.

    Args:
        embedding_service: EmbeddingService instance
        vector_store: PgVectorStore instance
        llm: Optional ChatOpenAI instance

    Returns:
        Compiled StateGraph
    """
    from research_agent.infrastructure.strategies.generation import (
        BasicGenerationStrategy,
        LongContextGenerationStrategy,
    )
    from research_agent.infrastructure.strategies.retrieval import (
        HybridRetrievalStrategy,
        VectorRetrievalStrategy,
    )

    deps = RAGGraphDependencies(
        retrieval_strategy=VectorRetrievalStrategy(
            embedding_service=embedding_service,
            vector_store=vector_store,
        ),
        generation_strategy=BasicGenerationStrategy(llm=llm),
        hybrid_retrieval_strategy=HybridRetrievalStrategy(
            embedding_service=embedding_service,
            vector_store=vector_store,
        ),
        long_context_generation_strategy=LongContextGenerationStrategy(llm=llm),
    )

    return create_rag_graph_v2(deps)
