"""Stream message use case (SSE streaming) - LangGraph implementation."""

import asyncio
import random
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any
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
from research_agent.infrastructure.vector_store.factory import get_vector_store
from research_agent.infrastructure.vector_store.langchain_pgvector import create_pgvector_retriever
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


class StreamingRefInjector:
    def __init__(self, default_video_source_id: str | None):
        self.default_video_source_id = default_video_source_id
        self.buffer = ""

    _time_pattern = re.compile(r"\[(?:TIME:)?(\d{1,2}:\d{2}(?::\d{2})?)\]")

    def process_token(self, token: str) -> str:
        self.buffer += token
        safe_text, remaining = self._split_safe(self.buffer)
        self.buffer = remaining
        return self._transform(safe_text)

    def flush(self) -> str:
        out = self._transform(self.buffer)
        self.buffer = ""
        return out

    def _split_safe(self, text: str) -> tuple[str, str]:
        last_open = text.rfind("[")
        if last_open == -1:
            return text, ""

        last_close = text.rfind("]")
        if last_close < last_open:
            return text[:last_open], text[last_open:]

        return text, ""

    def _time_str_to_seconds(self, time_str: str) -> int:
        try:
            parts = list(map(int, time_str.split(":")))
            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
            return 0
        except ValueError:
            return 0

    def _transform(self, text: str) -> str:
        if not text:
            return ""

        def repl(match: re.Match[str]) -> str:
            ts = match.group(1)
            if not self.default_video_source_id:
                # If no video context is active, just return the timestamp text
                return ts

            seconds = self._time_str_to_seconds(ts)
            # Format: [MM:SS](video-source://<id>?t=<seconds>)
            return f"[{ts}](video-source://{self.default_video_source_id}?t={seconds})"

        return self._time_pattern.sub(repl, text)


def _get_default_top_k() -> int:
    """Get default top_k from settings."""
    return settings.retrieval_top_k


@dataclass
class StreamMessageInput:
    """Input for stream message use case."""

    project_id: UUID
    message: str
    document_id: UUID | None = None
    user_id: str | None = None  # Optional user ID for data isolation
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
    context_node_ids: list[str] | None = (
        None  # IDs of canvas nodes explicitly dragged into context (DB lookup)
    )
    context_nodes: list[dict[str, Any]] | None = (
        None  # Direct context nodes with content (no DB lookup needed)
    )
    context_url_ids: list[str] | None = (
        None  # IDs of URL content to include as context (video transcripts, articles)
    )


@dataclass
class StreamEvent:
    """Streaming event."""

    type: str  # "token" | "sources" | "done" | "error" | "citations" | "status"
    content: str | None = None
    sources: list[SourceRef] | None = None
    citations: list[dict[str, Any]] | None = None  # Citations from long context mode
    step: str | None = (
        None  # For status events: rewriting, memory, analyzing, retrieving, ranking, generating
    )
    message: str | None = None  # Human-readable status message


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
        from .context_engine import ContextEngine
        from .stream_event_processor import StreamEventProcessor

        repo = SQLAlchemyChatRepository(self._session)

        # Initialize RAG Trace
        trace = RAGTrace(
            query=input.message,
            project_id=str(input.project_id),
            extra_context={
                "rag_mode": input.rag_mode,
                "model": self._model,
                "top_k": input.top_k,
                "hybrid_search": input.use_hybrid_search,
                "user_id": input.user_id,
            },
        )

        async with trace:
            try:
                # Step 1: Get chat history
                messages = await repo.get_history(
                    project_id=input.project_id,
                    limit=10,
                    user_id=input.user_id,
                )
                trace.log("HISTORY", messages_count=len(messages))

                # Step 2: Resolve context
                context_engine = ContextEngine(self._session)
                ctx = await context_engine.resolve(
                    project_id=input.project_id,
                    context_nodes=input.context_nodes,
                    context_node_ids=input.context_node_ids,
                    context_url_ids=input.context_url_ids,
                    chat_messages=messages,
                    user_id=input.user_id,
                )

                # Log context stats
                if ctx.canvas_node_count > 0 or ctx.url_resource_count > 0:
                    trace.log(
                        "CONTEXT",
                        canvas_nodes=ctx.canvas_node_count,
                        url_resources=ctx.url_resource_count,
                        context_chars=len(ctx.combined_context),
                    )

                # Step 3: Save user message
                await repo.save(
                    ChatMessage(
                        project_id=input.project_id,
                        role="user",
                        content=input.message,
                        context_refs=ctx.context_refs_for_user_message.to_dict(),
                        user_id=input.user_id,
                    )
                )

                # Step 4: Prepare chat history for rewrite
                chat_history = []
                if input.use_rewrite:
                    chat_history = [
                        (messages[i].content, messages[i + 1].content)
                        for i in range(0, len(messages) - 1, 2)
                        if i + 1 < len(messages)
                        and messages[i].role == "user"
                        and messages[i + 1].role == "ai"
                    ]

                # Step 5: Create retriever and LLM
                vector_store = get_vector_store(self._session)
                retriever = create_pgvector_retriever(
                    vector_store=vector_store,
                    embedding_service=self._embedding_service,
                    project_id=input.project_id,
                    k=input.top_k,
                    use_hybrid_search=input.use_hybrid_search,
                    document_id=input.document_id,
                    user_id=input.user_id,
                )

                llm = create_langchain_llm(
                    api_key=self._api_key,
                    model=self._model,
                    streaming=True,
                )

                # Step 6: Stream and process events
                ref_injector = StreamingRefInjector(ctx.default_video_source_id)
                processor = StreamEventProcessor(
                    ref_injector=ref_injector,
                    trace=trace,
                    initial_entities=ctx.active_entities,
                    initial_focus=ctx.current_focus,
                )

                async for event in stream_rag_response(
                    question=input.message,
                    retriever=retriever,
                    llm=llm,
                    chat_history=chat_history,
                    use_rewrite=input.use_rewrite,
                    use_llm_rewrite=settings.use_llm_rewrite,
                    use_intent_classification=input.use_intent_classification,
                    use_rerank=input.use_rerank,
                    use_grading=input.use_grading,
                    enable_intent_cache=settings.intent_cache_enabled,
                    rag_mode=input.rag_mode,
                    project_id=input.project_id,
                    embedding_service=self._embedding_service,
                    canvas_context=ctx.combined_context,
                    active_document_id=str(input.document_id) if input.document_id else None,
                    active_entities=ctx.active_entities,
                    current_focus=ctx.current_focus,
                    # Note: stream_rag_response signature might need update if we want to pass user_id down
                    # For now, most isolation is handled by retriever and context_engine
                ):
                    # Before handling done event, flush remaining content
                    if event.get("type") == "done":
                        remaining = processor.get_remaining_content()
                        if remaining:
                            yield StreamEvent(type="token", content=remaining)

                    result = processor.process(event)
                    if result:
                        yield result

                # Step 7: Save AI message
                stream_result = processor.get_result()
                if stream_result.full_response:
                    ai_message = ChatMessage(
                        project_id=input.project_id,
                        role="ai",
                        content=stream_result.full_response,
                        sources=stream_result.sources,
                        context_refs={
                            "entities": stream_result.active_entities,
                            "focus": stream_result.current_focus,
                        }
                        if stream_result.active_entities or stream_result.current_focus
                        else None,
                        user_id=input.user_id,
                    )
                    await repo.save(ai_message)

                # Step 8: Background tasks
                if (
                    self._should_evaluate()
                    and stream_result.full_response
                    and stream_result.retrieved_contexts
                ):
                    asyncio.create_task(
                        self._auto_evaluate(
                            question=input.message,
                            answer=stream_result.full_response,
                            contexts=stream_result.retrieved_contexts,
                            project_id=input.project_id,
                            chunking_strategy="dynamic",
                            retrieval_mode="hybrid" if input.use_hybrid_search else "vector",
                            llm=llm,
                            user_id=input.user_id,
                        )
                    )

                if stream_result.full_response:
                    asyncio.create_task(
                        self._store_memory(
                            project_id=input.project_id,
                            question=input.message,
                            answer=stream_result.full_response,
                            user_id=input.user_id,
                        )
                    )

            except Exception as e:
                import traceback

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
        contexts: list[str],
        project_id: UUID,
        chunking_strategy: str,
        retrieval_mode: str,
        llm: Any,
        user_id: str | None = None,
    ) -> None:
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
                        # Note: EvaluationLogger needs update to support user_id if we want to log it
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
        user_id: str | None = None,
    ) -> None:
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
                    user_id=user_id,
                )

            logger.info("[Memory] Memory stored successfully")

        except Exception as e:
            logger.error(f"[Memory] Failed to store memory: {e}", exc_info=True)
            # Don't raise - memory storage failure shouldn't affect user experience
