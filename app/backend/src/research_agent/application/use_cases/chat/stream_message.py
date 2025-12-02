"""Stream message use case (SSE streaming) - LangGraph implementation."""

from dataclasses import dataclass
from typing import AsyncIterator, List, Optional
from uuid import UUID

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
from research_agent.shared.utils.logger import logger


@dataclass
class SourceRef:
    """Source reference."""

    document_id: UUID
    page_number: int
    snippet: str
    similarity: float


@dataclass
class StreamMessageInput:
    """Input for stream message use case."""

    project_id: UUID
    message: str
    document_id: Optional[UUID] = None
    top_k: int = 5
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
                    sources = [
                        SourceRef(
                            document_id=UUID(doc.metadata["document_id"]),
                            page_number=doc.metadata["page_number"],
                            snippet=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                            similarity=doc.metadata.get("similarity", 0.0),
                        )
                        for doc in documents
                    ]

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

        except Exception as e:
            logger.error(f"Error in LangGraph RAG: {e}")
            yield StreamEvent(type="error", content=str(e))

