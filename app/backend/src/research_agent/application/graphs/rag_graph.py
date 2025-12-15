"""Agentic RAG workflow using LangGraph (Corrective RAG pattern)."""

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypedDict

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.outputs import LLMResult
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from research_agent.infrastructure.vector_store.langchain_pgvector import PGVectorRetriever
from research_agent.shared.utils.logger import logger

# Query rewrite cache (in-memory, simple LRU could be added later)
_rewrite_cache: dict[str, dict[str, str]] = {}

# Intent classification cache
_intent_cache: dict[str, dict[str, Any]] = {}


# --- Intent Classification System ---


class IntentType(str, Enum):
    """Question intent types for adaptive RAG strategies."""

    FACTUAL = "factual"  # "什么是X"、"X的定义" - Needs precise matching
    CONCEPTUAL = "conceptual"  # "如何理解X"、"X的原理" - Needs detailed context
    COMPARISON = "comparison"  # "X和Y的区别"、"X vs Y" - Needs multiple docs
    HOWTO = "howto"  # "如何做X"、"X的步骤" - Needs procedural content
    SUMMARY = "summary"  # "总结X"、"X的要点" - Needs broad coverage
    EXPLANATION = "explanation"  # "为什么X"、"X的原因" - Needs causal chain


@dataclass
class RetrievalStrategy:
    """Retrieval strategy configuration."""

    top_k: int  # Number of documents to retrieve
    min_similarity: float  # Minimum similarity threshold
    use_hybrid_search: bool  # Use hybrid search (vector + keyword)


@dataclass
class GenerationStrategy:
    """Generation strategy configuration."""

    style: str  # concise | detailed | structured
    max_length: int  # Maximum response length in tokens (approximate)
    system_prompt: str  # Custom system prompt for this intent


# Default strategies for each intent type
INTENT_STRATEGIES: dict[IntentType, tuple[RetrievalStrategy, GenerationStrategy]] = {
    IntentType.FACTUAL: (
        RetrievalStrategy(top_k=3, min_similarity=0.7, use_hybrid_search=True),
        GenerationStrategy(
            style="concise",
            max_length=150,
            system_prompt="You are a research assistant. Provide a concise, factual answer (1-2 sentences). Be direct and precise.",
        ),
    ),
    IntentType.CONCEPTUAL: (
        RetrievalStrategy(top_k=8, min_similarity=0.5, use_hybrid_search=False),
        GenerationStrategy(
            style="detailed",
            max_length=500,
            system_prompt="You are a research assistant. Provide a detailed explanation with principles and examples. Help the user understand the concept deeply.",
        ),
    ),
    IntentType.COMPARISON: (
        RetrievalStrategy(top_k=10, min_similarity=0.6, use_hybrid_search=True),
        GenerationStrategy(
            style="structured",
            max_length=400,
            system_prompt="You are a research assistant. Compare the items using a clear structure (table or bullet points). Highlight key similarities and differences.",
        ),
    ),
    IntentType.HOWTO: (
        RetrievalStrategy(top_k=5, min_similarity=0.6, use_hybrid_search=True),
        GenerationStrategy(
            style="structured",
            max_length=400,
            system_prompt="You are a research assistant. Provide step-by-step instructions in a numbered list format. Be clear and actionable.",
        ),
    ),
    IntentType.SUMMARY: (
        RetrievalStrategy(top_k=15, min_similarity=0.4, use_hybrid_search=False),
        GenerationStrategy(
            style="structured",
            max_length=500,
            system_prompt="You are a research assistant. Provide a comprehensive summary with key points in bullet format. Cover all important aspects.",
        ),
    ),
    IntentType.EXPLANATION: (
        RetrievalStrategy(top_k=8, min_similarity=0.5, use_hybrid_search=False),
        GenerationStrategy(
            style="detailed",
            max_length=500,
            system_prompt="You are a research assistant. Explain the reasoning and causality. Help the user understand why and how things work.",
        ),
    ),
}


# --- Logging Callback Handler ---


class LoggingCallbackHandler(BaseCallbackHandler):
    """Callback handler for logging LLM calls."""

    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any) -> None:
        """Log when LLM starts."""
        model = "unknown"
        if serialized:
            kwargs_dict = serialized.get("kwargs", {})
            # Try different keys that LangChain might use for model name
            model = (
                kwargs_dict.get("model")
                or kwargs_dict.get("model_name")
                or kwargs_dict.get("model_id")
                or "unknown"
            )
        logger.info(f"[LLM] Starting call to {model}")
        for i, prompt in enumerate(prompts):
            # Truncate long prompts
            truncated = prompt[:300] + "..." if len(prompt) > 300 else prompt
            logger.debug(f"[LLM] Prompt {i}: {truncated}")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Log when LLM ends."""
        if response and response.generations:
            for i, gen in enumerate(response.generations):
                for j, g in enumerate(gen):
                    content = g.text[:500] + "..." if len(g.text) > 500 else g.text
                    logger.info(f"[LLM] Raw response: {content}")

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Log LLM errors."""
        logger.error(f"[LLM] Error: {error}")

    def on_chain_start(
        self, serialized: dict[str, Any], inputs: dict[str, Any], **kwargs: Any
    ) -> None:
        """Log when chain starts."""
        chain_name = "unknown"
        if serialized:
            chain_name = (
                serialized.get("name") or serialized.get("id", ["unknown"])[-1]
                if serialized.get("id")
                else "unknown"
            )
        logger.debug(f"[Chain] Starting: {chain_name}")

    def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Log when chain ends."""
        logger.debug("[Chain] Completed")

    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Log chain errors."""
        logger.error(f"[Chain] Error: {error}")


# Create default callback handler
logging_callback = LoggingCallbackHandler()


def get_callbacks() -> list[BaseCallbackHandler]:
    """
    Get all callback handlers for LLM tracing.

    Returns a list containing:
    - LoggingCallbackHandler (always included)
    - LangfuseCallbackHandler (if enabled via LANGFUSE_ENABLED=true)
    """
    from research_agent.infrastructure.observability.langfuse_service import (
        create_langfuse_callback,
    )

    callbacks: list[BaseCallbackHandler] = [logging_callback]

    # Add Langfuse callback if enabled
    langfuse_cb = create_langfuse_callback()
    if langfuse_cb:
        callbacks.append(langfuse_cb)

    return callbacks


# --- State Schema ---


class GraphState(TypedDict):
    """State for the RAG graph."""

    question: str  # Original user question
    rewritten_question: str  # Rewritten question with context
    chat_history: list[tuple[str, str]]  # List of (human, ai) message tuples
    documents: list[Document]  # Retrieved documents
    reranked_documents: list[Document]  # Reranked documents
    generation: str  # Final answer
    filtered_documents: list[Document]  # Filtered relevant documents
    # Intent classification fields
    intent_type: str  # IntentType enum value
    intent_confidence: float  # Confidence score (0-1)
    retrieval_strategy: dict[str, Any]  # Dynamic retrieval parameters
    generation_strategy: dict[str, Any]  # Dynamic generation parameters
    # Long context mode fields
    long_context_content: str  # Formatted full document content for long context
    document_selection: dict[str, Any]  # Document selection result
    citations: list[dict[str, Any]]  # Parsed citations from generation
    rag_mode: str  # "traditional" | "long_context" | "hybrid"
    # Memory fields (Short-term + Long-term)
    session_summary: str  # Summarized conversation history (sliding window)
    retrieved_memories: list[dict[str, Any]]  # Semantically retrieved past discussions
    # Canvas context
    canvas_context: str  # Context from explicitly selected canvas nodes


# --- Grading Schema ---


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")


# --- Helper Functions for Query Rewriting ---


def needs_rewriting(question: str, chat_history: list[tuple[str, str]]) -> bool:
    """
    Smart check if query rewriting is actually needed.

    Returns True if:
    - Question contains pronouns/references (it, that, them, this, etc.)
    - Question is very short (< 10 chars) and has history
    - Question contains context-dependent words
    """
    if not chat_history:
        return False

    question_lower = question.lower()

    # Check for pronouns and references
    pronouns = [
        "it",
        "that",
        "them",
        "this",
        "these",
        "those",
        "he",
        "she",
        "they",
        "his",
        "her",
        "their",
    ]
    if any(pronoun in question_lower for pronoun in pronouns):
        return True

    # Very short questions with history likely need context
    if len(question.strip()) < 10:
        return True

    # Context-dependent words
    context_words = ["also", "again", "more", "another", "same", "different", "previous", "earlier"]
    if any(word in question_lower for word in context_words):
        return True

    return False


def get_cache_key(question: str, chat_history: list[tuple[str, str]]) -> str:
    """Generate cache key from question and recent history."""
    # Use last 3 turns for cache key
    recent_history = chat_history[-3:] if chat_history else []
    history_str = "|".join([f"{h[0]}:{h[1]}" for h in recent_history])
    key_str = f"{question}|{history_str}"
    return hashlib.md5(key_str.encode()).hexdigest()


def validate_rewrite(original: str, rewritten: str, max_expansion_ratio: float = 3.0) -> bool:
    """
    Validate rewrite quality.

    Returns False if:
    - Rewritten is too long compared to original (expansion ratio exceeded)
    - Rewritten is empty or too short
    - Rewritten is identical to original (no improvement)
    """
    if not rewritten or len(rewritten.strip()) < 3:
        logger.warning("Rewrite too short or empty")
        return False

    if rewritten.strip() == original.strip():
        logger.warning("Rewrite identical to original")
        return False

    # Check expansion ratio
    original_len = len(original)
    rewritten_len = len(rewritten)

    if original_len > 0:
        expansion_ratio = rewritten_len / original_len
        if expansion_ratio > max_expansion_ratio:
            logger.warning(
                f"Rewrite too long: {expansion_ratio:.2f}x expansion (max {max_expansion_ratio})"
            )
            return False

    return True


# --- Node Functions ---


async def transform_query(
    state: GraphState,
    llm: ChatOpenAI,
    enable_validation: bool = True,
    enable_cache: bool = True,
    max_expansion_ratio: float = 3.0,
) -> GraphState:
    """
    Enhanced query rewriting with validation and optimization.

    Args:
        state: Graph state containing question and chat_history
        llm: Language model for rewriting
        enable_validation: Validate rewrite quality before using
        enable_cache: Cache rewrite results
        max_expansion_ratio: Maximum allowed expansion ratio (rewritten/original length)
    """
    question = state["question"]
    chat_history = state.get("chat_history", [])

    # Quick return if no history
    if not chat_history:
        logger.info("No chat history, using original question")
        return {"rewritten_question": question, "question": question}

    # Smart skip: check if rewriting is actually needed
    if not needs_rewriting(question, chat_history):
        logger.info("Query doesn't need rewriting")
        return {"rewritten_question": question, "question": question}

    # Check cache
    cache_key = None
    if enable_cache:
        cache_key = get_cache_key(question, chat_history)
        if cache_key in _rewrite_cache:
            logger.info("Cache hit for query rewrite")
            return _rewrite_cache[cache_key]

    logger.info(f"Rewriting query with {len(chat_history)} history messages")

    # Build context
    history_context = "\n".join(
        [
            f"Human: {human}\nAssistant: {ai}"
            for human, ai in chat_history[-3:]  # Use last 3 turns
        ]
    )

    # Improved prompt with examples
    system_prompt = """You are a query rewriting assistant. Rewrite the user's question to be standalone.

Rules:
1. Resolve pronouns (it, that, them, etc.) with their actual referents
2. Include ONLY essential context from history
3. DO NOT add details the user didn't mention
4. Keep the question's original scope and openness
5. Output ONLY the rewritten question

Examples:
History: "什么是图谱模式" -> "图谱模式是..."
Question: "如何定义它？"
Rewrite: "如何定义图谱模式？" ✓
NOT: "如何通过配置文件定义图谱模式的Node对象？" ✗"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "History:\n{history}\n\nQuestion: {question}\n\nRewrite:"),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    try:
        rewritten = chain.invoke(
            {"history": history_context, "question": question},
            config={"callbacks": get_callbacks()},
        )
        rewritten = rewritten.strip()

        # Validate rewrite quality
        if enable_validation and not validate_rewrite(question, rewritten, max_expansion_ratio):
            logger.warning("Validation failed, using original")
            rewritten = question

        logger.info(f"[Rewrite] '{question}' -> '{rewritten}'")

        result = {"rewritten_question": rewritten, "question": question}

        # Cache result
        if enable_cache and cache_key:
            _rewrite_cache[cache_key] = result
            # Simple cache size limit (keep last 100 entries)
            if len(_rewrite_cache) > 100:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(_rewrite_cache))
                del _rewrite_cache[oldest_key]

        return result

    except Exception as e:
        logger.error(f"Rewrite failed: {e}")
        return {"rewritten_question": question, "question": question}


async def retrieve_memory(
    state: GraphState,
    session: Any,  # AsyncSession
    embedding_service: Any,  # EmbeddingService
    project_id: Any,  # UUID
    limit: int = 5,
    min_similarity: float = 0.6,
) -> GraphState:
    """
    Retrieve relevant memories (past discussions) for the current query.

    This enables semantic history retrieval - finding similar past Q&A interactions
    that may be relevant to the current question.

    Args:
        state: Graph state containing question
        session: Database session
        embedding_service: Service for generating embeddings
        project_id: Project UUID
        limit: Max number of memories to retrieve
        min_similarity: Minimum similarity threshold

    Returns:
        Updated state with retrieved_memories
    """
    from research_agent.domain.services.memory_service import MemoryService

    question = state.get("rewritten_question", state["question"])

    try:
        memory_service = MemoryService(
            session=session,
            embedding_service=embedding_service,
        )

        # Retrieve relevant memories
        memories = await memory_service.retrieve_relevant_memories(
            project_id=project_id,
            query=question,
            limit=limit,
            min_similarity=min_similarity,
        )

        # Convert to dict format for state
        retrieved_memories = [
            {
                "id": str(m.id),
                "content": m.content,
                "similarity": m.similarity,
                "metadata": m.metadata,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in memories
        ]

        logger.info(f"[Memory] Retrieved {len(retrieved_memories)} relevant memories")
        return {"retrieved_memories": retrieved_memories}

    except Exception as e:
        logger.error(f"[Memory] Failed to retrieve memories: {e}")
        return {"retrieved_memories": []}


async def get_session_summary(
    state: GraphState,
    session: Any,  # AsyncSession
    embedding_service: Any,  # EmbeddingService
    project_id: Any,  # UUID
) -> GraphState:
    """
    Get the session summary (summarized older conversation) for context.

    Args:
        state: Graph state
        session: Database session
        embedding_service: Service for generating embeddings
        project_id: Project UUID

    Returns:
        Updated state with session_summary
    """
    from research_agent.domain.services.memory_service import MemoryService

    try:
        memory_service = MemoryService(
            session=session,
            embedding_service=embedding_service,
        )

        summary = await memory_service.get_session_summary(project_id)
        logger.info(f"[Memory] Retrieved session summary: {len(summary)} chars")
        return {"session_summary": summary}

    except Exception as e:
        logger.error(f"[Memory] Failed to get session summary: {e}")
        return {"session_summary": ""}


def format_memory_for_context(state: GraphState) -> str:
    """
    Format memory information for inclusion in generation context.

    Args:
        state: Graph state with session_summary and retrieved_memories

    Returns:
        Formatted string for context injection
    """
    parts = []

    # Add session summary if available
    session_summary = state.get("session_summary", "")
    if session_summary:
        parts.append(f"## Conversation Summary\n{session_summary}")

    # Add relevant memories if available
    retrieved_memories = state.get("retrieved_memories", [])
    if retrieved_memories:
        memories_text = "\n\n".join(
            f"[Relevance: {m['similarity']:.2f}]\n{m['content']}" for m in retrieved_memories
        )
        parts.append(f"## Relevant Past Discussions\n{memories_text}")

    return "\n\n".join(parts) if parts else ""


async def classify_intent(
    state: GraphState,
    llm: ChatOpenAI,
    enable_cache: bool = True,
) -> GraphState:
    """
    Classify user question intent and select appropriate strategies.

    Args:
        state: Graph state containing question
        llm: Language model for classification
        enable_cache: Cache classification results

    Returns:
        Updated state with intent_type, intent_confidence, and strategies
    """
    from research_agent.infrastructure.llm.prompts.rag_prompt import (
        INTENT_CLASSIFICATION_PROMPT,
    )

    # Use rewritten question if available, otherwise use original
    question = state.get("rewritten_question", state["question"])

    # Check cache
    cache_key = None
    if enable_cache:
        cache_key = hashlib.md5(question.encode()).hexdigest()
        if cache_key in _intent_cache:
            logger.info("[Intent] Cache hit for intent classification")
            return _intent_cache[cache_key]

    logger.info(f"[Intent] Classifying intent for: {question[:50]}...")

    # Create classification prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", INTENT_CLASSIFICATION_PROMPT),
            ("human", "Question: {question}"),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    try:
        # Get classification result
        result = chain.invoke(
            {"question": question},
            config={"callbacks": get_callbacks()},
        )

        # Parse JSON response
        import json
        import re

        # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
        json_str = result.strip()
        code_fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(code_fence_pattern, json_str)
        if match:
            json_str = match.group(1).strip()

        result_data = json.loads(json_str)
        intent_type_str = result_data.get("intent", "factual")
        intent_confidence = result_data.get("confidence", 0.8)

        # Validate intent type
        try:
            intent_type = IntentType(intent_type_str)
        except ValueError:
            logger.warning(f"[Intent] Invalid intent type: {intent_type_str}, using FACTUAL")
            intent_type = IntentType.FACTUAL
            intent_confidence = 0.5

        logger.info(
            f"[Intent] Classified as {intent_type.value} (confidence: {intent_confidence:.2f})"
        )

        # Get strategies for this intent
        retrieval_strategy, generation_strategy = INTENT_STRATEGIES[intent_type]

        # Convert to dict for state
        result_state = {
            "intent_type": intent_type.value,
            "intent_confidence": intent_confidence,
            "retrieval_strategy": {
                "top_k": retrieval_strategy.top_k,
                "min_similarity": retrieval_strategy.min_similarity,
                "use_hybrid_search": retrieval_strategy.use_hybrid_search,
            },
            "generation_strategy": {
                "style": generation_strategy.style,
                "max_length": generation_strategy.max_length,
                "system_prompt": generation_strategy.system_prompt,
            },
        }

        # Cache result
        if enable_cache and cache_key:
            _intent_cache[cache_key] = result_state
            # Simple cache size limit (keep last 100 entries)
            if len(_intent_cache) > 100:
                oldest_key = next(iter(_intent_cache))
                del _intent_cache[oldest_key]

        return result_state

    except Exception as e:
        logger.error(f"[Intent] Classification failed: {e}, using default (FACTUAL)", exc_info=True)
        # Fallback to FACTUAL intent
        retrieval_strategy, generation_strategy = INTENT_STRATEGIES[IntentType.FACTUAL]
        return {
            "intent_type": IntentType.FACTUAL.value,
            "intent_confidence": 0.0,
            "retrieval_strategy": {
                "top_k": retrieval_strategy.top_k,
                "min_similarity": retrieval_strategy.min_similarity,
                "use_hybrid_search": retrieval_strategy.use_hybrid_search,
            },
            "generation_strategy": {
                "style": generation_strategy.style,
                "max_length": generation_strategy.max_length,
                "system_prompt": generation_strategy.system_prompt,
            },
        }


async def prepare_long_context(
    document_models: list[Any],  # DocumentModel from database
    session: Any,  # AsyncSession
) -> str:
    """
    Prepare formatted long context from full document content.

    Args:
        document_models: List of DocumentModel objects
        session: AsyncSession for database access

    Returns:
        Formatted long context string
    """
    from research_agent.domain.services.context_cache import ContextCacheService

    context_service = ContextCacheService(session)
    doc_sections = []

    for i, doc_model in enumerate(document_models, 1):
        doc_id = doc_model.id
        filename = doc_model.filename
        page_count = doc_model.page_count or 0

        # Get full context with metadata
        context_data = await context_service.get_context_with_metadata(doc_id)
        if not context_data or not context_data.get("content"):
            logger.warning(f"[LongContext] No full content for document {doc_id}")
            continue

        content = context_data["content"]

        # Build document section
        section = f"--- Document {i}: {filename} (ID: {doc_id})"
        if page_count > 0:
            section += f", {page_count} pages"
        section += " ---\n\n"
        section += content
        doc_sections.append(section)

    formatted_context = "\n\n".join(doc_sections)
    logger.info(f"[LongContext] Prepared context from {len(doc_sections)} documents")
    return formatted_context


async def retrieve_long_context(
    state: GraphState,
    retriever: PGVectorRetriever,
    document_selection: dict[str, Any],
    session: Any,  # AsyncSession
) -> GraphState:
    """
    Retrieve documents using long context mode.

    Args:
        state: Graph state
        retriever: PGVector retriever (for traditional retrieval fallback)
        document_selection: DocumentSelectionResult dict
        session: AsyncSession

    Returns:
        Updated state with documents
    """
    from sqlalchemy import select

    from research_agent.infrastructure.database.models import DocumentModel

    long_context_docs = document_selection.get("long_context_docs", [])
    retrieval_docs = document_selection.get("retrieval_docs", [])
    strategy = document_selection.get("strategy", "traditional")

    all_documents = []

    # Process long context documents
    if long_context_docs:
        logger.info(
            f"[LongContext] Processing {len(long_context_docs)} documents in long context mode"
        )

        # Get DocumentModel objects from database
        doc_ids = [doc.id for doc in long_context_docs]
        stmt = select(DocumentModel).where(DocumentModel.id.in_(doc_ids))
        result = await session.execute(stmt)
        doc_models = list(result.scalars().all())

        # Prepare long context
        long_context_content = await prepare_long_context(doc_models, session)

        # Create Document objects for long context docs
        for doc_model in doc_models:
            # Create a Document with full content
            doc = Document(
                page_content=doc_model.full_content or "",
                metadata={
                    "document_id": str(doc_model.id),
                    "filename": doc_model.filename,
                    "page_number": 0,  # Full document, no specific page
                    "source_type": "long_context",
                },
            )
            all_documents.append(doc)

        # Store long context content in state
        state["long_context_content"] = long_context_content

    # Process retrieval documents (traditional mode)
    if retrieval_docs:
        logger.info(f"[LongContext] Processing {len(retrieval_docs)} documents in retrieval mode")
        query = state.get("rewritten_question", state["question"])

        # Use traditional retrieval for these documents
        # Note: This is simplified - in practice, you might want to filter by document_id
        retrieved = await retriever._aget_relevant_documents(query)
        all_documents.extend(retrieved)

    logger.info(
        f"[LongContext] Total documents: {len(all_documents)} "
        f"(long_context: {len(long_context_docs)}, retrieval: {len(retrieval_docs)})"
    )

    return {
        "documents": all_documents,
        "rag_mode": strategy,
        "document_selection": document_selection,
    }


async def retrieve(state: GraphState, retriever: PGVectorRetriever) -> GraphState:
    """Retrieve documents from vector store using rewritten query and adaptive strategy."""
    # Use rewritten question if available, otherwise use original
    query = state.get("rewritten_question", state["question"])

    # Get retrieval strategy from state (set by intent classification)
    retrieval_strategy = state.get("retrieval_strategy", {})

    if retrieval_strategy:
        # Apply dynamic retrieval parameters
        top_k = retrieval_strategy.get("top_k", retriever.k)
        use_hybrid = retrieval_strategy.get("use_hybrid_search", False)

        logger.info(
            f"[Retrieve] Using adaptive strategy: top_k={top_k}, hybrid={use_hybrid}, "
            f"intent={state.get('intent_type', 'unknown')}"
        )

        # Update retriever parameters dynamically
        retriever.k = top_k
        retriever.use_hybrid_search = use_hybrid
    else:
        logger.info(f"[Retrieve] Using default strategy: top_k={retriever.k}")

    # Async retriever call
    documents = await retriever._aget_relevant_documents(query)

    logger.info(f"[Retrieve] Retrieved {len(documents)} documents")
    return {"documents": documents}


async def rerank(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """
    Rerank retrieved documents using LLM-based relevance scoring.
    Takes top-k documents and reranks them for better precision.
    """
    question = state.get("rewritten_question", state["question"])
    documents = state["documents"]

    if not documents:
        logger.warning("No documents to rerank")
        return {"reranked_documents": []}

    logger.info(f"Reranking {len(documents)} documents")

    # Prompt for scoring document relevance
    system_prompt = """You are a document relevance scorer. Rate how relevant the given document
is to answering the user's question on a scale of 0-10.

0 = Completely irrelevant
5 = Somewhat relevant
10 = Highly relevant and directly answers the question

Output ONLY a single number between 0-10. No explanation."""

    score_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Question: {question}\n\nDocument: {document}\n\nRelevance score (0-10):"),
        ]
    )

    chain = score_prompt | llm | StrOutputParser()

    # Score each document
    doc_scores = []
    for i, doc in enumerate(documents):
        try:
            # Truncate very long documents
            doc_content = (
                doc.page_content[:2000] if len(doc.page_content) > 2000 else doc.page_content
            )

            result = chain.invoke(
                {"question": question, "document": doc_content},
                config={"callbacks": get_callbacks()},
            )

            # Parse score
            try:
                score = float(result.strip().split()[0])  # Get first number
                score = max(0.0, min(10.0, score))  # Clamp to 0-10
            except (ValueError, IndexError):
                logger.warning(f"[Rerank] Failed to parse score from '{result}', using 5.0")
                score = 5.0

            doc_scores.append((score, doc))
            logger.debug(f"[Rerank] Doc {i + 1}: score={score}")
        except Exception as e:
            logger.warning(f"[Rerank] Error scoring doc {i + 1}: {e}")
            doc_scores.append((5.0, doc))  # Default mid-score

    # Sort by score (descending) and take top documents
    sorted_docs = sorted(doc_scores, key=lambda x: x[0], reverse=True)
    reranked = [doc for score, doc in sorted_docs if score >= 5.0]  # Filter low scores

    logger.info(f"Reranking complete: {len(reranked)}/{len(documents)} docs passed (score >= 5)")
    return {"reranked_documents": reranked}


def grade_documents(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """Grade retrieved documents for relevance."""
    # Defensive check for required fields
    if "question" not in state and "rewritten_question" not in state:
        logger.error(f"[Grade] Missing 'question' in state. Available keys: {list(state.keys())}")
        raise ValueError("State must contain 'question' or 'rewritten_question' field")

    question = state.get("rewritten_question", state.get("question", ""))
    # Use reranked documents if available, otherwise use retrieved documents
    documents = state.get("reranked_documents", state.get("documents", []))
    logger.info(
        f"[Grade] Grading {len(documents)} documents for relevance (question: '{question[:50]}...')"
    )

    # Simple prompt that asks for yes/no directly (no structured output needed)
    system_prompt = """You are a grader assessing relevance of a retrieved document to a user question.
If the document contains keyword(s) or semantic meaning related to the question, it is relevant.
Reply with ONLY 'yes' or 'no'. Nothing else."""

    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                "Document: {document}\n\nQuestion: {question}\n\nIs this document relevant? Reply only 'yes' or 'no':",
            ),
        ]
    )

    chain = grade_prompt | llm | StrOutputParser()

    # Grade each document
    filtered_docs = []
    for i, doc in enumerate(documents):
        try:
            logger.debug(f"[Grade] Grading document {i + 1}/{len(documents)}")

            # Truncate very long documents
            doc_content = (
                doc.page_content[:2000] if len(doc.page_content) > 2000 else doc.page_content
            )

            result = chain.invoke(
                {"question": question, "document": doc_content},
                config={"callbacks": get_callbacks()},
            )

            # Parse the response - look for yes/no
            result_lower = result.strip().lower()
            logger.info(f"[Grade] Document {i + 1} raw response: '{result_lower}'")

            is_relevant = "yes" in result_lower and "no" not in result_lower[:10]
            logger.info(
                f"[Grade] Document {i + 1} relevant: {is_relevant} (metadata: {doc.metadata})"
            )

            if is_relevant:
                filtered_docs.append(doc)
        except Exception as e:
            import traceback

            logger.warning(
                f"[Grade] Failed to grade document {i + 1}: {type(e).__name__}: {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            # On error, include the document (fail-safe: better to include than exclude)
            filtered_docs.append(doc)

    logger.info(f"Grading complete. {len(filtered_docs)}/{len(documents)} documents passed")
    return {"filtered_documents": filtered_docs}


def parse_citations(text: str) -> list[dict[str, Any]]:
    """
    Parse citations from generated text.

    Args:
        text: Generated text with citation markers

    Returns:
        List of citation dictionaries
    """
    from research_agent.domain.services.citation_service import CitationService

    citation_service = CitationService()
    markers = citation_service.parse_citation_markers(text)

    citations = []
    for marker in markers:
        cit = marker.citation
        citations.append(
            {
                "document_id": str(cit.document_id),
                "page_number": cit.page_number,
                "char_start": cit.char_start,
                "char_end": cit.char_end,
                "paragraph_index": cit.paragraph_index,
                "sentence_index": cit.sentence_index,
                "snippet": cit.snippet,
            }
        )

    return citations


def parse_xml_citations(
    text: str,
    doc_id_mapping: dict[str, str],
    doc_contents: dict[str, dict],
) -> list[dict[str, Any]]:
    """
    Parse XML citation tags from Mega-Prompt generated text.

    Args:
        text: Generated text with <cite> XML tags
        doc_id_mapping: Mapping from doc_XX to actual document UUIDs
        doc_contents: Dict of document info with full_content and page_map

    Returns:
        List of citation dictionaries with location information
    """
    from research_agent.domain.services.xml_citation_parser import XMLCitationParser
    from research_agent.utils.text_locator import TextLocator

    parser = XMLCitationParser()
    locator = TextLocator(fuzzy_threshold=85)

    parsed = parser.parse(text)
    citations = []

    for citation in parsed:
        # Map doc_id (doc_01) to actual document ID
        actual_doc_id = doc_id_mapping.get(citation.doc_id)
        if not actual_doc_id:
            logger.warning(f"[XMLCitations] Unknown doc_id: {citation.doc_id}")
            continue

        # Get document content for location
        doc_info = doc_contents.get(actual_doc_id, {})
        full_content = doc_info.get("full_content", "")
        page_map = doc_info.get("page_map", [])
        filename = doc_info.get("filename", "")

        # Locate quote in original document
        location = locator.locate(full_content, citation.quote, page_map)

        citations.append(
            {
                "doc_id": citation.doc_id,
                "document_id": actual_doc_id,
                "filename": filename,
                "quote": citation.quote,
                "conclusion": citation.conclusion,
                "char_start": location.char_start,
                "char_end": location.char_end,
                "page_number": location.page_number if location.page_number is not None else 1,
                "match_score": location.match_score,
                "match_type": location.match_type,
            }
        )

        if location.found:
            logger.debug(
                f"[XMLCitations] Located quote in {citation.doc_id}: "
                f"page={location.page_number}, chars={location.char_start}-{location.char_end}"
            )
        else:
            logger.warning(
                f"[XMLCitations] Could not locate quote in {citation.doc_id}: "
                f"{citation.quote[:50]}..."
            )

    return citations


class StreamingCitationParser:
    """Parser for streaming XML citations during LLM generation."""

    def __init__(
        self,
        doc_id_mapping: dict[str, str],
        doc_contents: dict[str, dict],
    ):
        self.doc_id_mapping = doc_id_mapping
        self.doc_contents = doc_contents
        self.buffer = ""
        self._parser = None
        self._locator = None

    def _get_parser(self):
        if self._parser is None:
            from research_agent.domain.services.xml_citation_parser import XMLCitationParser

            self._parser = XMLCitationParser()
        return self._parser

    def _get_locator(self):
        if self._locator is None:
            from research_agent.utils.text_locator import TextLocator

            self._locator = TextLocator(fuzzy_threshold=85)
        return self._locator

    def process_token(self, token: str) -> tuple[str, list[dict]]:
        """
        Process a token and return any completed citations.

        Args:
            token: New token from LLM

        Returns:
            Tuple of (text_to_emit, list_of_citations)
        """
        self.buffer += token

        parser = self._get_parser()
        locator = self._get_locator()

        citations_parsed, remaining, text_to_emit = parser.parse_streaming(self.buffer)
        self.buffer = remaining

        citations = []
        for citation in citations_parsed:
            # Map doc_id to actual document ID
            actual_doc_id = self.doc_id_mapping.get(citation.doc_id)
            if not actual_doc_id:
                continue

            # Get document content
            doc_info = self.doc_contents.get(actual_doc_id, {})
            full_content = doc_info.get("full_content", "")
            page_map = doc_info.get("page_map", [])
            filename = doc_info.get("filename", "")

            # Locate quote
            location = locator.locate(full_content, citation.quote, page_map)

            citations.append(
                {
                    "doc_id": citation.doc_id,
                    "document_id": actual_doc_id,
                    "filename": filename,
                    "quote": citation.quote,
                    "conclusion": citation.conclusion,
                    "char_start": location.char_start,
                    "char_end": location.char_end,
                    "page_number": location.page_number if location.page_number is not None else 1,
                    "match_score": location.match_score,
                }
            )

        return text_to_emit or "", citations

    def flush(self) -> str:
        """Flush remaining buffer."""
        remaining = self.buffer
        self.buffer = ""
        return remaining


def generate_long_context(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """Generate answer from long context with citation grounding."""
    from research_agent.config import get_settings
    from research_agent.infrastructure.llm.prompts.rag_prompt import (
        LONG_CONTEXT_SYSTEM_PROMPT,
        build_long_context_prompt,
    )

    settings = get_settings()
    question = state["question"]
    long_context_content = state.get("long_context_content", "")
    document_selection = state.get("document_selection", {})

    if not long_context_content:
        logger.warning("[GenerateLongContext] No long context content available")
        return {
            "generation": "I don't have enough relevant information to answer this question.",
            "citations": [],
        }

    logger.info(f"[GenerateLongContext] Generating with {len(long_context_content)} chars context")

    # Build documents list for prompt
    long_context_docs = document_selection.get("long_context_docs", [])
    documents = []
    for doc in long_context_docs:
        documents.append(
            {
                "document_id": str(doc.id),
                "filename": doc.filename,
                "content": long_context_content,  # Use prepared content
                "page_count": doc.page_count or 0,
            }
        )

    # Build prompt
    user_prompt = build_long_context_prompt(
        query=question,
        documents=documents,
        citation_format=settings.citation_format,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", LONG_CONTEXT_SYSTEM_PROMPT),
            ("human", user_prompt),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    try:
        generation = chain.invoke({"question": question}, config={"callbacks": get_callbacks()})
        logger.info(f"[GenerateLongContext] Response generated: {len(generation)} chars")

        # Parse citations
        citations = parse_citations(generation)

        logger.info(f"[GenerateLongContext] Parsed {len(citations)} citations")

        return {
            "generation": generation,
            "citations": citations,
        }
    except Exception as e:
        logger.error(f"[GenerateLongContext] Failed to generate response: {e}", exc_info=True)
        return {
            "generation": "I encountered an error while generating the response. Please try again.",
            "citations": [],
        }


def generate(state: GraphState, llm: ChatOpenAI) -> GraphState:
    """Generate answer from filtered documents with adaptive strategy."""
    # Check if we should use long context mode
    rag_mode = state.get("rag_mode", "traditional")
    if rag_mode in ("long_context", "hybrid") and state.get("long_context_content"):
        logger.info("[Generate] Using long context generation mode")
        return generate_long_context(state, llm)

    # Use original question for generation
    question = state["question"]
    documents = state.get(
        "filtered_documents", state.get("reranked_documents", state.get("documents", []))
    )

    # Get generation strategy from state (set by intent classification)
    generation_strategy = state.get("generation_strategy", {})

    logger.info(
        f"[Generate] Using {len(documents)} documents, "
        f"intent={state.get('intent_type', 'unknown')}, "
        f"style={generation_strategy.get('style', 'default')}"
    )

    # Check if we have documents
    if not documents:
        logger.warning("[Generate] No relevant documents found")
        return {
            "generation": "I don't have enough relevant information in the documents to answer this question.",
        }

    # Build context from documents
    doc_context = "\n\n".join([doc.page_content for doc in documents])

    # Build memory context (session summary + relevant past discussions)
    memory_context = format_memory_for_context(state)

    # Combine document context with memory context
    if memory_context:
        context = f"{memory_context}\n\n## Retrieved Documents\n{doc_context}"
        logger.info(f"[Generate] Including memory context: {len(memory_context)} chars")
    else:
        context = doc_context

    logger.debug(f"[Generate] Total context length: {len(context)} chars")

    # Use intent-specific system prompt if available
    if generation_strategy and "system_prompt" in generation_strategy:
        system_prompt = generation_strategy["system_prompt"]
        logger.info(f"[Generate] Using intent-specific prompt for {state.get('intent_type')}")
    else:
        # Default prompt with memory awareness
        system_prompt = """You are an assistant for question-answering tasks.
        Use the following pieces of retrieved context to answer the question.
        The context may include:
        - Conversation Summary: A summary of earlier parts of the conversation
        - Relevant Past Discussions: Similar questions and answers from previous sessions
        - Retrieved Documents: Information from the knowledge base
        
        Use all available context to provide the most helpful answer.
        If you don't know the answer, just say that you don't know.
        Use three sentences maximum and keep the answer concise."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Question: {question}\n\nContext: {context}\n\nAnswer:"),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    try:
        generation = chain.invoke(
            {"question": question, "context": context}, config={"callbacks": get_callbacks()}
        )
        logger.info(f"[Generate] Response generated: {len(generation)} chars")
    except Exception as e:
        logger.error(f"[Generate] Failed to generate response: {e}")
        generation = "I encountered an error while generating the response. Please try again."

    return {"generation": generation}


# --- Graph Builder ---


def create_rag_graph(
    retriever: PGVectorRetriever,
    llm: ChatOpenAI,
    use_rewrite: bool = True,
    use_intent_classification: bool = True,
    use_rerank: bool = True,
    use_grading: bool = True,
    enable_rewrite_validation: bool = True,
    enable_rewrite_cache: bool = True,
    enable_intent_cache: bool = True,
    max_expansion_ratio: float = 3.0,
) -> StateGraph:
    """
    Create the Enhanced Agentic RAG graph with intent-based strategies.

    Flow (all nodes enabled):
    1. Transform Query - Rewrite query with chat history context
    2. Classify Intent - Identify question type and select strategies
    3. Retrieve - Get documents from vector store (adaptive top_k and hybrid search)
    4. Rerank - LLM-based relevance scoring
    5. Grade Documents - Binary relevance check
    6. Generate - Create final answer (adaptive style and prompts)

    Args:
        retriever: PGVector retriever (can use hybrid search)
        llm: Language model for all LLM-based operations
        use_rewrite: Enable query rewriting with chat history
        use_intent_classification: Enable intent classification and adaptive strategies
        use_rerank: Enable LLM-based reranking
        use_grading: Enable binary relevance grading
        enable_rewrite_validation: Validate rewrite quality before using
        enable_rewrite_cache: Cache rewrite results to avoid redundant LLM calls
        enable_intent_cache: Cache intent classification results
        max_expansion_ratio: Maximum allowed expansion ratio (rewritten/original length)
    """
    workflow = StateGraph(GraphState)

    # Add nodes based on configuration
    if use_rewrite:
        # Create wrapper function with validation and cache settings
        async def transform_query_wrapper(state: GraphState) -> GraphState:
            return await transform_query(
                state,
                llm,
                enable_validation=enable_rewrite_validation,
                enable_cache=enable_rewrite_cache,
                max_expansion_ratio=max_expansion_ratio,
            )

        workflow.add_node("transform_query", transform_query_wrapper)

    if use_intent_classification:
        # Create wrapper function with cache settings
        async def classify_intent_wrapper(state: GraphState) -> GraphState:
            return await classify_intent(
                state,
                llm,
                enable_cache=enable_intent_cache,
            )

        workflow.add_node("classify_intent", classify_intent_wrapper)

    workflow.add_node("retrieve", lambda state: retrieve(state, retriever))

    if use_rerank:
        workflow.add_node("rerank", lambda state: rerank(state, llm))

    if use_grading:
        workflow.add_node("grade_documents", lambda state: grade_documents(state, llm))

    workflow.add_node("generate", lambda state: generate(state, llm))

    # Build graph edges
    if use_rewrite:
        workflow.set_entry_point("transform_query")
        if use_intent_classification:
            workflow.add_edge("transform_query", "classify_intent")
            workflow.add_edge("classify_intent", "retrieve")
        else:
            workflow.add_edge("transform_query", "retrieve")
    else:
        if use_intent_classification:
            workflow.set_entry_point("classify_intent")
            workflow.add_edge("classify_intent", "retrieve")
        else:
            workflow.set_entry_point("retrieve")

    if use_rerank:
        workflow.add_edge("retrieve", "rerank")
        if use_grading:
            workflow.add_edge("rerank", "grade_documents")
            workflow.add_edge("grade_documents", "generate")
        else:
            workflow.add_edge("rerank", "generate")
    else:
        if use_grading:
            workflow.add_edge("retrieve", "grade_documents")
            workflow.add_edge("grade_documents", "generate")
        else:
            workflow.add_edge("retrieve", "generate")

    workflow.add_edge("generate", END)

    return workflow.compile()


# --- Streaming Support ---


async def stream_rag_response(
    question: str,
    retriever: PGVectorRetriever,
    llm: ChatOpenAI,
    chat_history: list[tuple[str, str]] = None,
    use_rewrite: bool = True,
    use_intent_classification: bool = True,
    use_rerank: bool = True,
    use_grading: bool = True,
    enable_rewrite_validation: bool = True,
    enable_rewrite_cache: bool = True,
    enable_intent_cache: bool = True,
    max_expansion_ratio: float = 3.0,
    rag_mode: str = "traditional",
    project_id: Any = None,  # UUID
    session: Any = None,  # AsyncSession
    embedding_service: Any = None,  # EmbeddingService
    canvas_context: str = "",  # Context from canvas nodes
):
    """
    Stream RAG response token by token with intent-based adaptive strategies.

    Args:
        question: User question
        retriever: PGVector retriever
        llm: Language model
        chat_history: List of (human, ai) message tuples
        use_rewrite: Enable query rewriting
        use_intent_classification: Enable intent classification and adaptive strategies
        use_rerank: Enable reranking
        use_grading: Enable grading
        enable_rewrite_validation: Validate rewrite quality before using
        enable_rewrite_cache: Cache rewrite results to avoid redundant LLM calls
        enable_intent_cache: Cache intent classification results
        max_expansion_ratio: Maximum allowed expansion ratio (rewritten/original length)

    Yields:
        dict with 'type' and 'content' keys
    """
    logger.info(f"[Stream] Starting adaptive RAG stream for: {question[:50]}...")
    logger.info(f"[RAG Mode] Using RAG mode: {rag_mode}")

    # Initialize state
    state = {
        "question": question,
        "chat_history": chat_history or [],
        "canvas_context": canvas_context,
    }

    # Step 1: Query rewriting (optional)
    if use_rewrite and chat_history:
        logger.info("[Stream] Rewriting query...")
        rewrite_result = await transform_query(
            state,
            llm,
            enable_validation=enable_rewrite_validation,
            enable_cache=enable_rewrite_cache,
            max_expansion_ratio=max_expansion_ratio,
        )
        state.update(rewrite_result)  # Merge instead of replace
    else:
        state["rewritten_question"] = question

    # Step 1.5: Memory retrieval (semantic history) - if session and embedding_service available
    if session and embedding_service and project_id:
        logger.info("[Stream] Retrieving relevant memories...")
        try:
            # Get session summary (short-term working memory)
            summary_result = await get_session_summary(
                state,
                session=session,
                embedding_service=embedding_service,
                project_id=project_id,
            )
            state.update(summary_result)

            # Retrieve relevant past discussions (long-term episodic memory)
            memory_result = await retrieve_memory(
                state,
                session=session,
                embedding_service=embedding_service,
                project_id=project_id,
                limit=5,
                min_similarity=0.6,
            )
            state.update(memory_result)

            logger.info(
                f"[Stream] Memory context: summary={len(state.get('session_summary', ''))} chars, "
                f"memories={len(state.get('retrieved_memories', []))}"
            )
        except Exception as e:
            logger.warning(f"[Stream] Memory retrieval failed: {e}")
            state["session_summary"] = ""
            state["retrieved_memories"] = []

    # Step 2: Intent classification (optional)
    if use_intent_classification:
        logger.info("[Stream] Classifying intent...")
        intent_result = await classify_intent(
            state,
            llm,
            enable_cache=enable_intent_cache,
        )
        state.update(intent_result)  # Merge instead of replace
        logger.info(
            f"[Stream] Intent: {state.get('intent_type')} "
            f"(confidence: {state.get('intent_confidence', 0):.2f})"
        )

    # Step 3: Retrieve documents (with adaptive strategy or long context)
    if rag_mode in ("long_context", "auto") and session and project_id and embedding_service:
        from research_agent.config import get_settings
        from research_agent.domain.services.document_selector import DocumentSelectorService
        from research_agent.domain.services.token_estimator import TokenEstimator
        from research_agent.infrastructure.llm.model_config import calculate_available_tokens

        settings = get_settings()

        # Calculate available tokens
        max_tokens = calculate_available_tokens(
            settings.llm_model, settings.long_context_safety_ratio
        )
        min_tokens = settings.long_context_min_tokens

        logger.info(
            f"[RAG Mode] Long context mode enabled - max_tokens={max_tokens}, "
            f"min_tokens={min_tokens}, model={settings.llm_model}, "
            f"safety_ratio={settings.long_context_safety_ratio}"
        )

        try:
            # Create document selector
            token_estimator = TokenEstimator()
            doc_selector = DocumentSelectorService(
                session=session,
                embedding_service=embedding_service,
                token_estimator=token_estimator,
            )

            # Select documents for long context
            query = state.get("rewritten_question", state["question"])
            selection_result = await doc_selector.select_documents_for_query(
                query=query,
                project_id=project_id,
                max_tokens=max_tokens,
                min_tokens=min_tokens,
            )

            # Convert selection result to dict for state
            document_selection = {
                "long_context_docs": selection_result.long_context_docs,
                "retrieval_docs": selection_result.retrieval_docs,
                "strategy": selection_result.strategy,
                "total_tokens": selection_result.total_tokens,
                "reason": selection_result.reason,
            }

            logger.info(
                f"[RAG Mode] Document selection result: strategy={selection_result.strategy}, "
                f"long_context_docs={len(selection_result.long_context_docs)}, "
                f"retrieval_docs={len(selection_result.retrieval_docs)}, "
                f"total_tokens={selection_result.total_tokens}, "
                f"reason={selection_result.reason}"
            )

            # Retrieve using long context mode
            retrieve_result = await retrieve_long_context(
                state, retriever, document_selection, session
            )
            state.update(retrieve_result)
        except Exception as e:
            logger.warning(
                f"[Stream] Long context mode failed: {e}, falling back to traditional mode",
                exc_info=True,
            )
            retrieve_result = await retrieve(state, retriever)
            state.update(retrieve_result)
    else:
        logger.info(f"[RAG Mode] Using traditional retrieval mode")
        retrieve_result = await retrieve(state, retriever)
        state.update(retrieve_result)

    yield {"type": "sources", "documents": state["documents"]}

    # Step 4: Rerank (optional)
    if use_rerank:
        logger.info("[Stream] Reranking documents...")
        rerank_result = await rerank(state, llm)
        state.update(rerank_result)  # Merge instead of replace
        documents = state.get("reranked_documents", [])
    else:
        documents = state.get("documents", [])

    # Step 5: Grade documents (optional)
    if use_grading:
        logger.info("[Stream] Grading documents...")
        state["reranked_documents"] = documents  # Pass to grading
        logger.debug(f"[Stream] State keys before grading: {list(state.keys())}")
        grade_result = grade_documents(state, llm)
        state.update(grade_result)  # Merge instead of replace
        documents = state.get("filtered_documents", [])

    filtered_count = len(documents)
    logger.info(f"[Stream] {filtered_count} documents for generation")

    if filtered_count == 0:
        logger.warning("[Stream] No relevant documents found")
        yield {
            "type": "token",
            "content": "I don't have enough relevant information to answer this question.",
        }
        yield {"type": "done"}
        return

    # Step 6: Stream generation (with adaptive strategy or long context)
    current_rag_mode = state.get("rag_mode", "traditional")
    long_context_content = state.get("long_context_content", "")

    if current_rag_mode in ("long_context", "hybrid") and long_context_content:
        # Use long context generation
        logger.info(
            f"[RAG Mode] Using long context generation mode (content_length={len(long_context_content)} chars)"
        )
        from research_agent.config import get_settings
        from research_agent.infrastructure.llm.prompts.rag_prompt import (
            LONG_CONTEXT_SYSTEM_PROMPT,
            build_long_context_prompt,
            build_mega_prompt,
            get_document_id_mapping,
        )

        settings = get_settings()
        document_selection = state.get("document_selection", {})
        long_context_docs = document_selection.get("long_context_docs", [])

        # Get citation mode from settings (defaults to xml_quote for Mega-Prompt)
        citation_mode = getattr(settings, "mega_prompt_citation_mode", "xml_quote")
        intent_type = state.get("intent_type", "factual")

        # Build documents list for prompt
        documents_for_prompt = []
        doc_contents = {}  # For citation localization

        for doc in long_context_docs:
            doc_id = str(doc.id)
            doc_info = {
                "document_id": doc_id,
                "filename": doc.filename,
                "content": doc.full_content or long_context_content,
                "page_count": doc.page_count or 0,
            }
            documents_for_prompt.append(doc_info)

            # Store content info for citation localization
            doc_contents[doc_id] = {
                "full_content": doc.full_content or "",
                "page_map": doc.parsing_metadata.get("page_map", [])
                if doc.parsing_metadata
                else [],
                "filename": doc.filename,
            }

        # Choose prompt format based on citation mode
        if citation_mode == "xml_quote":
            # Use Mega-Prompt with XML citations
            logger.info("[RAG Mode] Using Mega-Prompt with XML citations")

            mega_prompt = build_mega_prompt(
                query=question,
                documents=documents_for_prompt,
                intent_type=intent_type,
                role="research assistant",
            )

            # Get doc ID mapping (doc_01 -> actual UUID)
            doc_id_mapping = get_document_id_mapping(documents_for_prompt)

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("human", mega_prompt),
                ]
            )

            # Create streaming LLM with callback (includes Langfuse if enabled)
            streaming_llm = llm.with_config({"streaming": True, "callbacks": get_callbacks()})
            chain = prompt | streaming_llm | StrOutputParser()

            # Stream tokens with real-time citation parsing
            token_count = 0
            full_response = ""
            citation_parser = StreamingCitationParser(doc_id_mapping, doc_contents)

            try:
                async for token in chain.astream({}):
                    token_count += 1
                    full_response += token

                    # Process token for citations
                    text_to_emit, citations = citation_parser.process_token(token)

                    # Emit text (may be delayed due to buffering)
                    if text_to_emit:
                        yield {"type": "token", "content": text_to_emit}

                    # Emit any completed citations
                    for citation in citations:
                        yield {"type": "citation", "data": citation}

                # Flush remaining buffer
                remaining = citation_parser.flush()
                if remaining:
                    yield {"type": "token", "content": remaining}

                logger.info(f"[Stream] Mega-Prompt generation complete: {token_count} tokens")

                # Parse any remaining citations from full response
                all_citations = parse_xml_citations(full_response, doc_id_mapping, doc_contents)
                if all_citations:
                    yield {"type": "citations", "citations": all_citations}
                    logger.info(f"[Stream] Total {len(all_citations)} XML citations parsed")

            except Exception as e:
                import traceback

                logger.error(
                    f"[Stream] Mega-Prompt generation error: {type(e).__name__}: {e}\n"
                    f"Question: {question[:100]}...\n"
                    f"Traceback:\n{traceback.format_exc()}",
                    exc_info=True,
                )
                yield {"type": "token", "content": f"\n\n[Error: {type(e).__name__}: {str(e)}]"}
        else:
            # Use traditional long context prompt
            user_prompt = build_long_context_prompt(
                query=question,
                documents=documents_for_prompt,
                citation_format=settings.citation_format,
            )

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", LONG_CONTEXT_SYSTEM_PROMPT),
                    ("human", user_prompt),
                ]
            )

            # Create streaming LLM with callback (includes Langfuse if enabled)
            streaming_llm = llm.with_config({"streaming": True, "callbacks": get_callbacks()})
            chain = prompt | streaming_llm | StrOutputParser()

            # Stream tokens
            token_count = 0
            full_response = ""
            try:
                async for token in chain.astream({"question": question}):
                    token_count += 1
                    full_response += token
                    yield {"type": "token", "content": token}
                logger.info(f"[Stream] Long context generation complete: {token_count} tokens")

                # Parse citations from response
                citations = parse_citations(full_response)
                if citations:
                    yield {"type": "citations", "citations": citations}
                    logger.info(f"[Stream] Parsed {len(citations)} citations")
            except Exception as e:
                import traceback

                logger.error(
                    f"[Stream] Long context generation error: {type(e).__name__}: {e}\n"
                    f"Question: {question[:100]}...\n"
                    f"Context length: {len(long_context_content)} chars\n"
                    f"Traceback:\n{traceback.format_exc()}",
                    exc_info=True,
                )
                yield {"type": "token", "content": f"\n\n[Error: {type(e).__name__}: {str(e)}]"}

        # End of long context generation - important to return here!
        yield {"type": "done"}
        return

    else:
        # Use traditional generation
        doc_context = "\n\n".join([doc.page_content for doc in documents])

    # Build memory context (session summary + relevant past discussions)
    memory_context = format_memory_for_context(state)
    canvas_context = state.get("canvas_context", "")

    # Combine document context with memory context and canvas context
    context_parts = []

    if canvas_context:
        context_parts.append(
            f"## User Specified Context (from Canvas)\nThe user has explicitly selected the following nodes as context. Prioritize this information:\n\n{canvas_context}"
        )
        logger.info(f"[Generate] Including canvas context: {len(canvas_context)} chars")

    if memory_context:
        context_parts.append(memory_context)
        logger.info(f"[Generate] Including memory context: {len(memory_context)} chars")

    if doc_context:
        context_parts.append(f"## Retrieved Documents\n{doc_context}")

    context = "\n\n".join(context_parts)

    logger.debug(f"[Generate] Total context length: {len(context)} chars")

    # Use intent-specific system prompt if available
    generation_strategy = state.get("generation_strategy", {})
    if generation_strategy and "system_prompt" in generation_strategy:
        system_prompt = generation_strategy["system_prompt"]
        logger.info(f"[Generate] Using intent-specific prompt for {state.get('intent_type')}")
    else:
        system_prompt = """You are an assistant for question-answering tasks.
        Use the following pieces of retrieved context to answer the question.
        The context may include:
        - User Specified Context: Information explicitly selected by the user (Highest Priority)
        - Conversation Summary: A summary of earlier parts of the conversation
        - Relevant Past Discussions: Similar questions and answers from previous sessions
        - Retrieved Documents: Information from the knowledge base
        
        Use all available context to provide the most helpful answer.
        If you don't know the answer, just say that you don't know.
        Use three sentences maximum and keep the answer concise."""

    # Create prompt and chain (moved outside the else block to fix the bug)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Question: {question}\n\nContext: {context}\n\nAnswer:"),
        ]
    )

    # Create streaming LLM with callback (includes Langfuse if enabled)
    streaming_llm = llm.with_config({"streaming": True, "callbacks": get_callbacks()})
    chain = prompt | streaming_llm | StrOutputParser()

    # Stream tokens
    token_count = 0
    try:
        async for token in chain.astream({"question": question, "context": context}):
            token_count += 1
            yield {"type": "token", "content": token}
        logger.info(f"[Stream] Generation complete: {token_count} tokens")
    except Exception as e:
        import traceback

        logger.error(
            f"[Stream] Generation error: {type(e).__name__}: {e}\n"
            f"Question: {question[:100]}...\n"
            f"Context length: {len(context)} chars\n"
            f"Traceback:\n{traceback.format_exc()}",
            exc_info=True,
        )
        yield {"type": "token", "content": f"\n\n[Error: {type(e).__name__}: {str(e)}]"}

    yield {"type": "done"}
