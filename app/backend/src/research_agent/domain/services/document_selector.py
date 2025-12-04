"""Document selection service for long context mode."""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.services.token_estimator import TokenEstimator
from research_agent.infrastructure.database.models import DocumentModel
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.shared.utils.logger import logger


@dataclass
class DocumentSelectionResult:
    """Result of document selection for long context mode."""

    long_context_docs: List[DocumentModel]  # Documents to use with long context
    retrieval_docs: List[DocumentModel]  # Documents to use with traditional retrieval
    strategy: str  # "long_context" | "traditional" | "hybrid"
    total_tokens: int  # Total tokens for selected documents
    reason: str  # Selection reason for logging


class DocumentSelectorService:
    """Service for intelligently selecting documents for long context mode."""

    def __init__(
        self,
        session: AsyncSession,
        embedding_service: EmbeddingService,
        token_estimator: TokenEstimator,
    ):
        self._session = session
        self._embedding_service = embedding_service
        self._token_estimator = token_estimator

    async def select_documents_for_query(
        self,
        query: str,
        project_id: UUID,
        max_tokens: int,
        min_tokens: int = 10000,
    ) -> DocumentSelectionResult:
        """
        Intelligently select documents for query using similarity ranking.

        Args:
            query: User query
            project_id: Project ID
            max_tokens: Maximum available tokens
            min_tokens: Minimum tokens to use long context mode

        Returns:
            DocumentSelectionResult with selected documents and strategy
        """
        # Get all documents for the project
        stmt = select(DocumentModel).where(
            DocumentModel.project_id == project_id,
            DocumentModel.status == "completed",  # Only completed documents
            DocumentModel.full_content.isnot(None),  # Must have full content
        )
        result = await self._session.execute(stmt)
        documents = list(result.scalars().all())

        if not documents:
            logger.info(f"[DocumentSelector] No documents found for project {project_id}")
            return DocumentSelectionResult(
                long_context_docs=[],
                retrieval_docs=[],
                strategy="traditional",
                total_tokens=0,
                reason="No documents available",
            )

        # Calculate token counts first
        doc_token_counts = []
        for doc in documents:
            token_count = doc.content_token_count or 0
            # If token count not cached, estimate it
            if token_count == 0 and doc.full_content:
                token_count = self._token_estimator.estimate_tokens(doc.full_content)
                # Cache the token count (async update would be better, but this is simpler)
                doc.content_token_count = token_count
            doc_token_counts.append((doc, token_count))

        # Calculate total tokens
        total_available_tokens = sum(token_count for _, token_count in doc_token_counts)

        # Optimization: Skip embedding if we can fit all documents
        # or if there's only one document
        if len(documents) == 1:
            # Single document: no need for similarity ranking
            logger.info("[DocumentSelector] Single document - skipping embedding calculation")
            doc_scores = [(doc, 1.0, token_count) for doc, token_count in doc_token_counts]
        elif total_available_tokens <= max_tokens:
            # All documents fit: no need for similarity ranking
            logger.info(
                f"[DocumentSelector] All {len(documents)} documents fit in context "
                f"({total_available_tokens} tokens) - skipping embedding calculation"
            )
            doc_scores = [(doc, 1.0, token_count) for doc, token_count in doc_token_counts]
        else:
            # Multiple documents and need to select: use embedding for similarity ranking
            logger.info(
                f"[DocumentSelector] Multiple documents ({len(documents)}) exceed context "
                f"({total_available_tokens} > {max_tokens} tokens) - using embedding for selection"
            )
            query_embedding = await self._embedding_service.embed(query)
            doc_scores = []

            for doc, token_count in doc_token_counts:
                # Get average similarity from document chunks
                similarity = await self._get_document_similarity(doc.id, query_embedding)
                doc_scores.append((doc, similarity, token_count))

            # Sort by similarity (descending)
            doc_scores.sort(key=lambda x: x[1], reverse=True)

        # Select documents up to max_tokens
        selected_docs = []
        total_tokens = 0

        for doc, similarity, token_count in doc_scores:
            # Skip documents that are too small (use traditional mode for them)
            if token_count < min_tokens:
                logger.debug(
                    f"[DocumentSelector] Skipping document {doc.id} "
                    f"(too small: {token_count} < {min_tokens})"
                )
                continue

            # Check if adding this document would exceed max_tokens
            if total_tokens + token_count > max_tokens:
                logger.debug(
                    f"[DocumentSelector] Cannot add document {doc.id} "
                    f"(would exceed: {total_tokens + token_count} > {max_tokens})"
                )
                break

            selected_docs.append(doc)
            total_tokens += token_count

        # Determine strategy
        if not selected_docs:
            strategy = "traditional"
            reason = "No suitable documents for long context mode"
        elif len(selected_docs) == len(documents):
            strategy = "long_context"
            reason = f"All {len(documents)} documents fit in context ({total_tokens} tokens)"
        else:
            strategy = "hybrid"
            reason = (
                f"Selected {len(selected_docs)}/{len(documents)} documents "
                f"for long context ({total_tokens}/{max_tokens} tokens), "
                f"rest use traditional retrieval"
            )

        # Get documents not selected for long context
        selected_ids = {doc.id for doc in selected_docs}
        retrieval_docs = [doc for doc, _, _ in doc_scores if doc.id not in selected_ids]

        logger.info(
            f"[DocumentSelector] Strategy: {strategy}, "
            f"Long context: {len(selected_docs)}, "
            f"Retrieval: {len(retrieval_docs)}, "
            f"Total tokens: {total_tokens}"
        )

        return DocumentSelectionResult(
            long_context_docs=selected_docs,
            retrieval_docs=retrieval_docs,
            strategy=strategy,
            total_tokens=total_tokens,
            reason=reason,
        )

    async def _get_document_similarity(
        self, document_id: UUID, query_embedding: list[float]
    ) -> float:
        """
        Get document similarity by averaging top chunk similarities.

        Args:
            document_id: Document ID
            query_embedding: Query embedding vector

        Returns:
            Average similarity score (0-1)
        """
        from sqlalchemy import bindparam, text

        from research_agent.infrastructure.database.models import DocumentChunkModel

        # Use pgvector distance operator
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # Get top 5 chunks for this document and average their similarities
        query = text("""
            SELECT 
                1 - (embedding <=> cast(:embedding as vector)) AS similarity
            FROM document_chunks
            WHERE document_id = cast(:document_id as uuid)
                AND embedding IS NOT NULL
            ORDER BY embedding <=> cast(:embedding as vector)
            LIMIT 5
        """).bindparams(
            bindparam("embedding", value=embedding_str),
            bindparam("document_id", value=str(document_id)),
        )

        result = await self._session.execute(query)
        similarities = [float(row.similarity) for row in result.fetchall()]

        if not similarities:
            return 0.0

        # Return average similarity
        return sum(similarities) / len(similarities)

    def calculate_total_context_size(self, documents: List[DocumentModel]) -> int:
        """
        Calculate total context size in tokens.

        Args:
            documents: List of documents

        Returns:
            Total token count
        """
        total = 0
        for doc in documents:
            if doc.content_token_count:
                total += doc.content_token_count
            elif doc.full_content:
                total += self._token_estimator.estimate_tokens(doc.full_content)
        return total
