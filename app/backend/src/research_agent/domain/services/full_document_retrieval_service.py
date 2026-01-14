"""Full document retrieval service for Mega-Prompt RAG mode.

This service supports retrieving complete document content for the Mega-Prompt
approach, with automatic context size management to prevent token overflow.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.config import get_settings
from research_agent.domain.services.token_estimator import TokenEstimator
from research_agent.infrastructure.database.models import DocumentModel
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.vector_store.base import SearchResult, VectorStore
from research_agent.shared.utils.logger import logger


class RetrievalMode(str, Enum):
    """Document retrieval modes."""

    CHUNKS = "chunks"  # Traditional chunk-based retrieval
    FULL_DOCUMENT = "full_document"  # Retrieve full document content
    AUTO = "auto"  # Automatically select based on document size


@dataclass
class FullDocumentRetrievalConfig:
    """Configuration for full document retrieval."""

    mode: RetrievalMode = RetrievalMode.AUTO
    top_k_documents: int = 3  # Max number of documents to include in full mode
    token_limit: int = 30000  # Max tokens for context (conservative limit)
    min_similarity: float = 0.5  # Minimum chunk similarity to consider document
    fallback_to_chunks: bool = True  # Fallback to chunks if documents exceed limit


@dataclass
class DocumentContent:
    """Container for retrieved document content."""

    document_id: UUID
    filename: str
    full_content: str
    token_count: int
    page_count: int
    summary: str | None = None
    parsing_metadata: dict[str, Any] | None = None

    @property
    def page_map(self) -> list[dict[str, Any]]:
        """Get page map from parsing metadata."""
        if self.parsing_metadata:
            return self.parsing_metadata.get("page_map", [])
        return []


@dataclass
class RetrievalResult:
    """Result of full document retrieval."""

    documents: list[DocumentContent]
    mode_used: RetrievalMode
    total_tokens: int
    was_truncated: bool = False
    truncation_reason: str | None = None
    chunk_results: list[SearchResult] | None = None  # Fallback chunk results


class FullDocumentRetrievalService:
    """
    Service for retrieving full document content for Mega-Prompt RAG.

    This service implements an adaptive retrieval strategy:
    1. First, performs chunk-based search to identify relevant documents
    2. Retrieves full content of top-K documents
    3. Applies dynamic context degradation if total tokens exceed limit:
       - Strategy A: Keep top-1 document full, truncate others
       - Strategy B: Fallback to chunk-based retrieval
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        config: FullDocumentRetrievalConfig | None = None,
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.config = config or FullDocumentRetrievalConfig()
        self.token_estimator = TokenEstimator()
        self._settings = get_settings()

    async def retrieve(
        self,
        query: str,
        project_id: UUID,
        session: AsyncSession,
        mode: RetrievalMode | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        """
        Retrieve documents for RAG based on the specified mode.

        Args:
            query: User query
            project_id: Project ID
            session: Database session
            mode: Retrieval mode (defaults to config mode)
            top_k: Number of documents to retrieve (defaults to config)

        Returns:
            RetrievalResult with documents and metadata
        """
        effective_mode = mode or self.config.mode
        effective_top_k = top_k or self.config.top_k_documents

        logger.info(
            f"[FullDocRetrieval] Starting retrieval - mode={effective_mode}, "
            f"top_k={effective_top_k}, project_id={project_id}"
        )

        # Step 1: Perform chunk-based search to identify relevant documents
        chunk_results = await self._search_chunks(query, project_id, effective_top_k * 3)

        if not chunk_results:
            logger.warning("[FullDocRetrieval] No chunks found for query")
            return RetrievalResult(
                documents=[],
                mode_used=RetrievalMode.CHUNKS,
                total_tokens=0,
                chunk_results=[],
            )

        # Extract unique document IDs from chunk results, ordered by relevance
        doc_ids = self._get_top_document_ids(chunk_results, effective_top_k)

        logger.info(f"[FullDocRetrieval] Identified {len(doc_ids)} relevant documents")

        # Step 2: Decide retrieval mode
        if effective_mode == RetrievalMode.CHUNKS:
            return RetrievalResult(
                documents=[],
                mode_used=RetrievalMode.CHUNKS,
                total_tokens=0,
                chunk_results=chunk_results,
            )

        # Step 3: Retrieve full document content
        documents = await self._fetch_documents(doc_ids, session)

        if not documents:
            logger.warning("[FullDocRetrieval] No documents found in database")
            return RetrievalResult(
                documents=[],
                mode_used=RetrievalMode.CHUNKS,
                total_tokens=0,
                chunk_results=chunk_results,
            )

        # Step 4: Calculate total tokens and apply degradation if needed
        total_tokens = sum(doc.token_count for doc in documents)

        logger.info(
            f"[FullDocRetrieval] Total tokens: {total_tokens}, limit: {self.config.token_limit}"
        )

        # Step 5: Apply adaptive context strategy if needed
        if total_tokens > self.config.token_limit:
            logger.warning(
                f"[FullDocRetrieval] Context size {total_tokens} exceeds limit "
                f"{self.config.token_limit}. Applying adaptive strategy."
            )
            documents, was_truncated, truncation_reason = await self._apply_degradation(
                documents, chunk_results
            )
            total_tokens = sum(doc.token_count for doc in documents)

            return RetrievalResult(
                documents=documents,
                mode_used=RetrievalMode.FULL_DOCUMENT,
                total_tokens=total_tokens,
                was_truncated=was_truncated,
                truncation_reason=truncation_reason,
                chunk_results=chunk_results if self.config.fallback_to_chunks else None,
            )

        return RetrievalResult(
            documents=documents,
            mode_used=RetrievalMode.FULL_DOCUMENT,
            total_tokens=total_tokens,
            was_truncated=False,
            chunk_results=chunk_results,
        )

    async def _search_chunks(self, query: str, project_id: UUID, limit: int) -> list[SearchResult]:
        """Search for relevant chunks using vector store."""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.embed(query)

            # Search vector store
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                project_id=project_id,
                limit=limit,
            )

            # Filter by minimum similarity
            results = [r for r in results if r.similarity >= self.config.min_similarity]

            logger.info(f"[FullDocRetrieval] Found {len(results)} relevant chunks")
            return results

        except Exception as e:
            logger.error(f"[FullDocRetrieval] Chunk search failed: {e}")
            return []

    def _get_top_document_ids(self, chunk_results: list[SearchResult], top_k: int) -> list[UUID]:
        """Extract top-K unique document IDs from chunk results, ordered by relevance."""
        seen = set()
        doc_ids = []

        for result in chunk_results:
            doc_id = result.document_id
            if doc_id not in seen:
                seen.add(doc_id)
                doc_ids.append(doc_id)
                if len(doc_ids) >= top_k:
                    break

        return doc_ids

    async def _fetch_documents(
        self, doc_ids: list[UUID], session: AsyncSession
    ) -> list[DocumentContent]:
        """Fetch full document content from database."""
        if not doc_ids:
            return []

        stmt = select(DocumentModel).where(DocumentModel.id.in_(doc_ids))
        result = await session.execute(stmt)
        doc_models = list(result.scalars().all())

        # Create DocumentContent objects and preserve order from doc_ids
        doc_map = {doc.id: doc for doc in doc_models}
        documents = []

        for doc_id in doc_ids:
            if doc_id in doc_map:
                doc = doc_map[doc_id]
                content = doc.full_content or ""
                token_count = doc.content_token_count or self.token_estimator.estimate_tokens(
                    content
                )

                documents.append(
                    DocumentContent(
                        document_id=doc.id,
                        filename=doc.filename,
                        full_content=content,
                        token_count=token_count,
                        page_count=doc.page_count or 0,
                        summary=doc.summary,
                        parsing_metadata=doc.parsing_metadata,
                    )
                )

        return documents

    async def _apply_degradation(
        self,
        documents: list[DocumentContent],
        chunk_results: list[SearchResult],
    ) -> tuple[list[DocumentContent], bool, str]:
        """
        Apply adaptive context degradation strategy.

        Strategy:
        1. Keep the most relevant document (top-1) in full
        2. If still over limit, truncate content
        3. If fallback enabled, return chunk results instead
        """
        if not documents:
            return documents, False, None

        # Strategy A: Keep only top-1 document
        top_doc = documents[0]

        if top_doc.token_count <= self.config.token_limit:
            logger.info(
                f"[FullDocRetrieval] Degradation: Keeping only top-1 document "
                f"({top_doc.token_count} tokens)"
            )
            return [top_doc], True, "Reduced to top-1 document to fit context limit"

        # Strategy B: Truncate top document content
        if top_doc.token_count > self.config.token_limit:
            truncated_content = self._truncate_content(
                top_doc.full_content, self.config.token_limit
            )
            truncated_doc = DocumentContent(
                document_id=top_doc.document_id,
                filename=top_doc.filename,
                full_content=truncated_content,
                token_count=self.token_estimator.estimate_tokens(truncated_content),
                page_count=top_doc.page_count,
                summary=top_doc.summary,
                parsing_metadata=top_doc.parsing_metadata,
            )
            logger.info(
                f"[FullDocRetrieval] Degradation: Truncated top document "
                f"from {top_doc.token_count} to {truncated_doc.token_count} tokens"
            )
            return [truncated_doc], True, "Truncated document content to fit context limit"

        return [top_doc], True, "Applied context degradation"

    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """Truncate content to fit within token limit."""
        # Rough approximation: 1 token ≈ 4 characters for English/Chinese mixed text
        # Use a conservative ratio
        max_chars = max_tokens * 3  # Conservative estimate

        if len(content) <= max_chars:
            return content

        # Truncate and add ellipsis
        truncated = content[:max_chars]

        # Try to truncate at a sentence boundary
        last_period = max(
            truncated.rfind("。"),
            truncated.rfind("."),
            truncated.rfind("\n\n"),
        )
        if last_period > max_chars * 0.8:  # Only if we keep at least 80%
            truncated = truncated[: last_period + 1]

        return truncated + "\n\n[... content truncated due to length ...]"


# Utility function for creating service with default config
def create_full_document_retrieval_service(
    vector_store: VectorStore,
    embedding_service: EmbeddingService,
    mode: str = "auto",
    token_limit: int = 30000,
) -> FullDocumentRetrievalService:
    """Create a configured FullDocumentRetrievalService."""
    config = FullDocumentRetrievalConfig(
        mode=RetrievalMode(mode),
        token_limit=token_limit,
    )
    return FullDocumentRetrievalService(
        vector_store=vector_store,
        embedding_service=embedding_service,
        config=config,
    )
