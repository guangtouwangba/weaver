"""Stream message use case (SSE streaming) - LangGraph implementation."""

import asyncio
import random
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.application.graphs.rag_graph import stream_rag_response
from research_agent.config import get_settings
from research_agent.domain.entities.chat import ChatMessage
from research_agent.infrastructure.database.repositories.sqlalchemy_chat_repo import (
    SQLAlchemyChatRepository,
)
from research_agent.infrastructure.database.session import get_async_session
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.evaluation.evaluation_logger import EvaluationLogger
from research_agent.infrastructure.evaluation.ragas_service import RagasEvaluationService
from research_agent.infrastructure.llm.openrouter import create_langchain_llm
from research_agent.infrastructure.resource_resolver import ResourceResolver
from research_agent.infrastructure.vector_store.langchain_pgvector import create_pgvector_retriever
from research_agent.infrastructure.vector_store.pgvector import PgVectorStore
from research_agent.shared.utils.logger import logger
from research_agent.shared.utils.rag_trace import RAGTrace

settings = get_settings()


@dataclass
class SourceRef:
    """Source reference."""

    document_id: UUID
    page_number: int
    snippet: str
    similarity: float


def _get_default_top_k() -> int:
    """Get default top_k from settings."""
    return settings.retrieval_top_k


@dataclass
class StreamMessageInput:
    """Input for stream message use case."""

    project_id: UUID
    message: str
    document_id: Optional[UUID] = None
    session_id: Optional[UUID] = None  # Chat session ID
    top_k: int = field(default_factory=_get_default_top_k)
    use_hybrid_search: bool = False  # Enable hybrid search (vector + keyword)
    use_rewrite: bool = True  # Enable query rewriting with chat history
    use_intent_classification: bool = field(
        default_factory=lambda: settings.intent_classification_enabled
    )  # Enable intent-based adaptive strategies
    use_rerank: bool = False  # Enable LLM-based reranking (expensive)
    use_grading: bool = True  # Enable binary relevance grading
    rag_mode: str = field(
        default_factory=lambda: settings.rag_mode
    )  # RAG mode: traditional | long_context | auto
    context_node_ids: Optional[List[str]] = (
        None  # IDs of canvas nodes explicitly dragged into context (DB lookup)
    )
    context_nodes: Optional[List[dict]] = (
        None  # Direct context nodes with content (no DB lookup needed)
    )
    context_url_ids: Optional[List[str]] = (
        None  # IDs of URL content to include as context (video transcripts, articles)
    )


@dataclass
class StreamEvent:
    """Streaming event."""

    type: str  # "token" | "sources" | "done" | "error" | "citations" | "status"
    content: Optional[str] = None
    sources: Optional[List[SourceRef]] = None
    citations: Optional[List[dict]] = None  # Citations from long context mode
    step: Optional[str] = (
        None  # For status events: rewriting, memory, analyzing, retrieving, ranking, generating
    )
    message: Optional[str] = None  # Human-readable status message


class StreamMessageUseCase:
    """Use case for streaming chat message with RAG using LangGraph."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_service: EmbeddingService,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
    ):
        self._session = session
        self._embedding_service = embedding_service
        self._api_key = api_key
        self._model = model

        # Initialize evaluation services if enabled
        self._evaluation_enabled = settings.evaluation_enabled
        self._evaluation_sample_rate = settings.evaluation_sample_rate

        if self._evaluation_enabled:
            logger.info(
                f"[Auto-Eval] Evaluation enabled with sample rate: {settings.evaluation_sample_rate}"
            )

    async def execute(self, input: StreamMessageInput) -> AsyncIterator[StreamEvent]:
        """Execute the use case with streaming using LangGraph."""
        repo = SQLAlchemyChatRepository(self._session)

        # Get or create default session if not provided
        session_id = input.session_id
        if session_id is None:
            default_session = await repo.get_or_create_default_session(input.project_id)
            session_id = default_session.id

        # Initialize RAG Trace for end-to-end observability
        trace = RAGTrace(
            query=input.message,
            project_id=str(input.project_id),
            session_id=str(session_id),
            extra_context={
                "rag_mode": input.rag_mode,
                "model": self._model,
                "top_k": input.top_k,
                "hybrid_search": input.use_hybrid_search,
            },
        )

        # Build context references for the user message
        context_refs = None
        if input.context_url_ids or input.context_node_ids or input.context_nodes:
            context_refs = {}

            # Fetch URL content metadata for display
            if input.context_url_ids:
                try:
                    from uuid import UUID as UUID_type

                    from research_agent.infrastructure.database.repositories.sqlalchemy_url_content_repo import (
                        SQLAlchemyUrlContentRepository,
                    )

                    url_repo = SQLAlchemyUrlContentRepository(self._session)
                    urls = []
                    for url_id in input.context_url_ids:
                        try:
                            url_content = await url_repo.get_by_id(UUID_type(url_id))
                            if url_content:
                                urls.append(
                                    {
                                        "id": str(url_content.id),
                                        "title": url_content.title,
                                        "platform": url_content.platform,
                                        "url": url_content.url,
                                    }
                                )
                        except Exception as e:
                            logger.warning(f"Failed to fetch URL content {url_id}: {e}")
                            urls.append({"id": url_id, "title": "URL"})
                    context_refs["urls"] = urls
                except Exception as e:
                    logger.error(f"Failed to fetch URL metadata: {e}")
                    context_refs["url_ids"] = input.context_url_ids

            if input.context_node_ids:
                context_refs["node_ids"] = input.context_node_ids
            if input.context_nodes:
                # Store simplified node info for display (id, title only)
                context_refs["nodes"] = [
                    {"id": n.get("id"), "title": n.get("title", "Untitled")}
                    for n in input.context_nodes
                ]

        # Save User Message with context references
        await repo.save(
            ChatMessage(
                project_id=input.project_id,
                session_id=session_id,
                role="user",
                content=input.message,
                context_refs=context_refs,
            )
        )

        full_response = ""
        response_sources: list = []
        retrieved_documents = []  # Store documents for evaluation
        retrieved_contexts = []  # Store context strings for evaluation
        token_count = 0  # Track generated tokens

        # Enter trace context for the main RAG pipeline
        async with trace:
            try:
                # Get chat history for query rewriting and thinking path
                chat_history = []
                messages = await repo.get_history(
                    project_id=input.project_id,
                    session_id=session_id,
                    limit=10,
                )
                trace.log("HISTORY", messages_count=len(messages))

                # === Canvas Context Retrieval ===
                canvas_context = ""
                canvas_node_count = 0
                url_count = 0

                # Priority 1: Use directly passed context_nodes (no DB lookup needed)
                if input.context_nodes:
                    context_parts = []
                    for node in input.context_nodes:
                        title = node.get("title", "Untitled")
                        content = node.get("content", "")
                        if content:
                            context_parts.append(f"## Node: {title}\n{content}")

                    if context_parts:
                        canvas_context = "\n\n".join(context_parts)
                        canvas_node_count = len(context_parts)

                # Priority 2: Fallback to context_node_ids (DB lookup)
                elif input.context_node_ids:
                    try:
                        from research_agent.infrastructure.database.repositories.sqlalchemy_canvas_repo import (
                            SQLAlchemyCanvasRepository,
                        )

                        canvas_repo = SQLAlchemyCanvasRepository(self._session)
                        canvas = await canvas_repo.find_by_project(input.project_id)

                        if canvas:
                            context_parts = []
                            for node_id in input.context_node_ids:
                                node = canvas.find_node(node_id)
                                if node:
                                    context_parts.append(f"## Node: {node.title}\n{node.content}")

                            if context_parts:
                                canvas_context = "\n\n".join(context_parts)
                                canvas_node_count = len(context_parts)
                    except Exception as e:
                        logger.error(
                            f"[CanvasContext] Failed to retrieve canvas nodes: {e}", exc_info=True
                        )

                # === URL Content Context Retrieval (via ResourceResolver) ===
                url_context = ""
                if input.context_url_ids:
                    try:
                        resolver = ResourceResolver(self._session)
                        url_uuids = [UUID(uid) for uid in input.context_url_ids]
                        resources = await resolver.resolve_many(url_uuids)

                        url_context_parts = []
                        max_content_length = 50000  # Truncate long transcripts/articles

                        for resource in resources:
                            if resource.has_content:
                                # Truncate content if too long
                                content = resource.display_content
                                if len(content) > max_content_length:
                                    content = (
                                        content[:max_content_length] + "\n\n[Content truncated...]"
                                    )

                                # Build context with source info
                                source_info = (
                                    f"Source: {resource.source_url}\n\n"
                                    if resource.source_url
                                    else ""
                                )
                                url_context_parts.append(
                                    f"{resource.get_formatted_content().split(chr(10), 1)[0]}\n"
                                    f"{source_info}{content}"
                                )

                        if url_context_parts:
                            url_context = "\n\n---\n\n".join(url_context_parts)
                            url_count = len(url_context_parts)

                    except Exception as e:
                        logger.error(
                            f"[ResourceContext] Failed to retrieve URL content: {e}", exc_info=True
                        )

                # Combine canvas context and URL context
                if url_context:
                    if canvas_context:
                        canvas_context = canvas_context + "\n\n---\n\n" + url_context
                    else:
                        canvas_context = url_context

                # Log context retrieval
                if canvas_node_count > 0 or url_count > 0:
                    trace.log(
                        "CONTEXT",
                        canvas_nodes=canvas_node_count,
                        url_resources=url_count,
                        context_chars=len(canvas_context),
                    )

                if input.use_rewrite:
                    # Convert to (human, ai) tuples
                    chat_history = [
                        (messages[i].content, messages[i + 1].content)
                        for i in range(0, len(messages) - 1, 2)
                        if i + 1 < len(messages)
                        and messages[i].role == "user"
                        and messages[i + 1].role == "ai"
                    ]

                # Create vector store and retriever with hybrid search option
                vector_store = PgVectorStore(self._session)
                retriever = create_pgvector_retriever(
                    vector_store=vector_store,
                    embedding_service=self._embedding_service,
                    project_id=input.project_id,
                    k=input.top_k,
                    use_hybrid_search=input.use_hybrid_search,
                )

                # Create LangChain LLM
                llm = create_langchain_llm(
                    api_key=self._api_key,
                    model=self._model,
                    streaming=True,
                )

                # Stream response from enhanced LangGraph pipeline with intent classification
                async for event in stream_rag_response(
                    question=input.message,
                    retriever=retriever,
                    llm=llm,
                    chat_history=chat_history,
                    use_rewrite=input.use_rewrite,
                    use_llm_rewrite=settings.use_llm_rewrite,  # NEW: Use LLM rewrite or rule-based expansion
                    use_intent_classification=input.use_intent_classification,
                    use_rerank=input.use_rerank,
                    use_grading=input.use_grading,
                    enable_intent_cache=settings.intent_cache_enabled,
                    rag_mode=input.rag_mode,
                    project_id=input.project_id,
                    session=self._session,
                    embedding_service=self._embedding_service,
                    canvas_context=canvas_context,
                ):
                    if event["type"] == "sources":
                        # Convert LangChain documents to SourceRef
                        documents = event.get("documents", [])
                        retrieved_documents = documents  # Store for evaluation

                        # Calculate top similarity for logging
                        top_similarity = max(
                            [doc.metadata.get("similarity", 0.0) for doc in documents],
                            default=0.0,
                        )

                        # Update trace metrics for final summary
                        trace.metrics["docs_count"] = len(documents)
                        trace.metrics["top_similarity"] = round(top_similarity, 3)

                        sources = [
                            SourceRef(
                                document_id=UUID(doc.metadata["document_id"]),
                                page_number=doc.metadata["page_number"],
                                snippet=doc.page_content[:200] + "..."
                                if len(doc.page_content) > 200
                                else doc.page_content,
                                similarity=doc.metadata.get("similarity", 0.0),
                            )
                            for doc in documents
                        ]

                        # Store contexts for evaluation
                        retrieved_contexts = [doc.page_content for doc in documents]

                        # Store for saving to DB
                        response_sources = [
                            {
                                "document_id": str(s.document_id),
                                "page_number": s.page_number,
                                "snippet": s.snippet,
                                "similarity": s.similarity,
                            }
                            for s in sources
                        ]

                        yield StreamEvent(type="sources", sources=sources)
                    elif event["type"] == "citations":
                        # Handle citations from long context mode
                        citations_data = event.get("citations", [])
                        trace.metrics["citations_count"] = len(citations_data)
                    elif event["type"] == "status":
                        # Forward thinking status events to frontend
                        yield StreamEvent(
                            type="status",
                            step=event.get("step"),
                            message=event.get("message"),
                        )
                    elif event["type"] == "token":
                        content = event.get("content", "")
                        full_response += content
                        token_count += 1
                        yield StreamEvent(type="token", content=content)
                    elif event["type"] == "done":
                        # Log final token count
                        trace.metrics["token_count"] = token_count
                        trace.metrics["answer_length"] = len(full_response)
                        yield StreamEvent(type="done")

                # Save AI Message
                ai_message = None
                if full_response:
                    ai_message = ChatMessage(
                        project_id=input.project_id,
                        session_id=session_id,
                        role="ai",
                        content=full_response,
                        sources=response_sources,
                    )
                    await repo.save(ai_message)

                # === Auto-Evaluation (Async, Non-blocking) ===
                if self._should_evaluate() and full_response and retrieved_contexts:
                    # Trigger evaluation in background (don't await)
                    asyncio.create_task(
                        self._auto_evaluate(
                            question=input.message,
                            answer=full_response,
                            contexts=retrieved_contexts,
                            project_id=input.project_id,
                            chunking_strategy="dynamic",  # Could be detected from config
                            retrieval_mode="hybrid" if input.use_hybrid_search else "vector",
                            llm=llm,
                        )
                    )

                # === Memory Ingestion (Async, Non-blocking) ===
                # Store the Q&A pair as a memory for future semantic retrieval
                if full_response:
                    asyncio.create_task(
                        self._store_memory(
                            project_id=input.project_id,
                            question=input.message,
                            answer=full_response,
                        )
                    )

            except Exception as e:
                import traceback

                # Log error to trace
                trace.log(
                    "ERROR",
                    error_type=type(e).__name__,
                    error_message=str(e)[:200],
                )

                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "query": input.message[:100],
                    "project_id": str(input.project_id),
                    "config": {
                        "use_hybrid_search": input.use_hybrid_search,
                        "use_rewrite": input.use_rewrite,
                        "use_rerank": input.use_rerank,
                        "use_grading": input.use_grading,
                        "top_k": input.top_k,
                    },
                }
                logger.error(
                    f"Error in LangGraph RAG: {e}\n"
                    f"Error Type: {type(e).__name__}\n"
                    f"Query: {input.message[:100]}...\n"
                    f"Config: {error_details['config']}\n"
                    f"Traceback:\n{traceback.format_exc()}",
                    exc_info=True,
                )
                yield StreamEvent(type="error", content=f"{type(e).__name__}: {str(e)}")

    def _should_evaluate(self) -> bool:
        """Determine if evaluation should be triggered (based on sampling rate)."""
        if not self._evaluation_enabled:
            return False

        # Sample based on rate (e.g., 0.1 = 10% of queries)
        return random.random() < self._evaluation_sample_rate

    async def _auto_evaluate(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        project_id: UUID,
        chunking_strategy: str,
        retrieval_mode: str,
        llm,
    ):
        """
        Auto-evaluate RAG quality in background.

        This runs asynchronously and doesn't block the user response.
        Uses its own database session to avoid connection leak issues.
        """
        try:
            logger.info(f"[Auto-Eval] Starting evaluation for: {question[:50]}...")

            # Create Ragas service with the same LLM
            ragas_service = RagasEvaluationService(
                llm=llm,
                embeddings=self._embedding_service,
            )

            # Evaluate
            metrics = await ragas_service.evaluate_single(
                question=question,
                answer=answer,
                contexts=contexts,
            )

            if metrics:
                logger.info(f"[Auto-Eval] Metrics: {metrics}")

                # Log to database and Loki using a NEW session
                # (the request session may be closed by the time this background task runs)
                async with get_async_session() as eval_session:
                    evaluation_logger = EvaluationLogger(eval_session)
                    await evaluation_logger.log_evaluation(
                        question=question,
                        answer=answer,
                        contexts=contexts,
                        metrics=metrics,
                        project_id=project_id,
                        chunking_strategy=chunking_strategy,
                        retrieval_mode=retrieval_mode,
                        evaluation_type="realtime",
                    )

                logger.info("[Auto-Eval] Evaluation logged successfully")
            else:
                logger.warning("[Auto-Eval] No metrics returned")

        except Exception as e:
            logger.error(f"[Auto-Eval] Failed: {e}", exc_info=True)
            # Don't raise - evaluation failure shouldn't affect user experience

    async def _store_memory(
        self,
        project_id: UUID,
        question: str,
        answer: str,
    ):
        """
        Store Q&A pair as a memory for future semantic retrieval.

        This runs asynchronously and doesn't block the user response.
        Enables long-term episodic memory - the system can recall similar
        past discussions when handling new queries.
        Uses its own database session to avoid connection leak issues.
        """
        try:
            from research_agent.domain.services.memory_service import MemoryService

            logger.info(f"[Memory] Storing memory for: {question[:50]}...")

            # Use a NEW session for background task
            # (the request session may be closed by the time this runs)
            async with get_async_session() as memory_session:
                memory_service = MemoryService(
                    session=memory_session,
                    embedding_service=self._embedding_service,
                )

                await memory_service.store_memory(
                    project_id=project_id,
                    question=question,
                    answer=answer,
                    metadata={
                        "source": "chat",
                        "model": self._model,
                    },
                )

            logger.info("[Memory] Memory stored successfully")

        except Exception as e:
            logger.error(f"[Memory] Failed to store memory: {e}", exc_info=True)
            # Don't raise - memory storage failure shouldn't affect user experience
