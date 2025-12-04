"""Stream message use case (SSE streaming) - LangGraph implementation."""

from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional
from uuid import UUID
import asyncio
import random

from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.application.graphs.rag_graph import stream_rag_response
from research_agent.domain.entities.chat import ChatMessage
from research_agent.infrastructure.database.repositories.sqlalchemy_chat_repo import (
    SQLAlchemyChatRepository,
)
from research_agent.infrastructure.llm.langchain_openrouter import create_langchain_llm
from research_agent.infrastructure.vector_store.langchain_pgvector import create_pgvector_retriever
from research_agent.infrastructure.vector_store.pgvector import PgVectorStore
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.evaluation.ragas_service import RagasEvaluationService
from research_agent.infrastructure.evaluation.evaluation_logger import EvaluationLogger
from research_agent.config import get_settings
from research_agent.shared.utils.logger import logger

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
    top_k: int = field(default_factory=_get_default_top_k)
    use_hybrid_search: bool = False  # Enable hybrid search (vector + keyword)
    use_rewrite: bool = True  # Enable query rewriting with chat history
    use_rerank: bool = False  # Enable LLM-based reranking (expensive)
    use_grading: bool = True  # Enable binary relevance grading


@dataclass
class StreamEvent:
    """Streaming event."""

    type: str  # "token" | "sources" | "done" | "error"
    content: Optional[str] = None
    sources: Optional[List[SourceRef]] = None


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
            logger.info("[Auto-Eval] Evaluation enabled with sample rate: {settings.evaluation_sample_rate}")
            # Initialize Ragas service (will be created per request to use same LLM)
            self._evaluation_logger = EvaluationLogger(session)

    async def execute(self, input: StreamMessageInput) -> AsyncIterator[StreamEvent]:
        """Execute the use case with streaming using LangGraph."""
        logger.info(f"Processing query with LangGraph: {input.message[:50]}...")

        repo = SQLAlchemyChatRepository(self._session)

        # Save User Message
        await repo.save(
            ChatMessage(project_id=input.project_id, role="user", content=input.message)
        )

        full_response = ""
        response_sources: list = []
        retrieved_documents = []  # Store documents for evaluation
        retrieved_contexts = []  # Store context strings for evaluation

        try:
            # Get chat history for query rewriting
            chat_history = []
            if input.use_rewrite:
                messages = await repo.get_history(input.project_id, limit=10)
                # Convert to (human, ai) tuples
                chat_history = [
                    (messages[i].content, messages[i+1].content)
                    for i in range(0, len(messages)-1, 2)
                    if i+1 < len(messages) and messages[i].role == "user" and messages[i+1].role == "ai"
                ]
                logger.info(f"Retrieved {len(chat_history)} chat history pairs")
            
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
            
            # Stream response from enhanced LangGraph pipeline
            async for event in stream_rag_response(
                question=input.message,
                retriever=retriever,
                llm=llm,
                chat_history=chat_history,
                use_rewrite=input.use_rewrite,
                use_rerank=input.use_rerank,
                use_grading=input.use_grading,
            ):
                if event["type"] == "sources":
                    # Convert LangChain documents to SourceRef
                    documents = event.get("documents", [])
                    retrieved_documents = documents  # Store for evaluation
                    
                    sources = [
                        SourceRef(
                            document_id=UUID(doc.metadata["document_id"]),
                            page_number=doc.metadata["page_number"],
                            snippet=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
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
                elif event["type"] == "token":
                    content = event.get("content", "")
                    full_response += content
                    yield StreamEvent(type="token", content=content)
                elif event["type"] == "done":
                    yield StreamEvent(type="done")
            
            # Save AI Message
            if full_response:
                await repo.save(
                    ChatMessage(
                        project_id=input.project_id,
                        role="ai",
                        content=full_response,
                        sources=response_sources,
                    )
                )
            
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

        except Exception as e:
            import traceback
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
                }
            }
            logger.error(
                f"Error in LangGraph RAG: {e}\n"
                f"Error Type: {type(e).__name__}\n"
                f"Query: {input.message[:100]}...\n"
                f"Config: {error_details['config']}\n"
                f"Traceback:\n{traceback.format_exc()}",
                exc_info=True
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
                
                # Log to database and Loki
                await self._evaluation_logger.log_evaluation(
                    question=question,
                    answer=answer,
                    contexts=contexts,
                    metrics=metrics,
                    project_id=project_id,
                    chunking_strategy=chunking_strategy,
                    retrieval_mode=retrieval_mode,
                    evaluation_type="realtime",
                )
                
                logger.info(f"[Auto-Eval] Evaluation logged successfully")
            else:
                logger.warning(f"[Auto-Eval] No metrics returned")
                
        except Exception as e:
            logger.error(f"[Auto-Eval] Failed: {e}", exc_info=True)
            # Don't raise - evaluation failure shouldn't affect user experience

