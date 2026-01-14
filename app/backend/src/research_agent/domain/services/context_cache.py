"""Context cache service for long context mode."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.infrastructure.database.models import DocumentModel
from research_agent.shared.utils.logger import logger


class ContextCacheService:
    """Service for managing full document context cache."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_full_context(self, document_id: UUID) -> str | None:
        """
        Get full document content (with caching).

        Args:
            document_id: Document ID

        Returns:
            Full document content or None if not available
        """
        stmt = select(DocumentModel.full_content).where(DocumentModel.id == document_id)
        result = await self._session.execute(stmt)
        content = result.scalar_one_or_none()

        if content:
            logger.debug(f"[ContextCache] Retrieved full content for document {document_id}")
        else:
            logger.warning(f"[ContextCache] No full content cached for document {document_id}")

        return content

    async def get_context_with_metadata(self, document_id: UUID) -> dict | None:
        """
        Get full document content with metadata.

        Args:
            document_id: Document ID

        Returns:
            Dict with 'content', 'token_count', and 'metadata' keys, or None
        """
        stmt = select(
            DocumentModel.full_content,
            DocumentModel.content_token_count,
            DocumentModel.parsing_metadata,
        ).where(DocumentModel.id == document_id)

        result = await self._session.execute(stmt)
        row = result.first()

        if not row or not row.full_content:
            return None

        return {
            "content": row.full_content,
            "token_count": row.content_token_count,
            "metadata": row.parsing_metadata or {},
        }

    async def should_use_full_context(
        self, document_id: UUID, max_tokens: int, min_tokens: int = 10000
    ) -> bool:
        """
        Determine if full context should be used for a document.

        Args:
            document_id: Document ID
            max_tokens: Maximum available tokens
            min_tokens: Minimum tokens to use long context mode

        Returns:
            True if full context should be used
        """
        stmt = select(DocumentModel.content_token_count).where(DocumentModel.id == document_id)
        result = await self._session.execute(stmt)
        token_count = result.scalar_one_or_none()

        if token_count is None:
            logger.warning(f"[ContextCache] No token count for document {document_id}")
            return False

        # Check if document meets criteria
        if token_count < min_tokens:
            logger.debug(
                f"[ContextCache] Document {document_id} too small ({token_count} < {min_tokens}), "
                "use traditional mode"
            )
            return False

        if token_count > max_tokens:
            logger.debug(
                f"[ContextCache] Document {document_id} too large ({token_count} > {max_tokens}), "
                "use traditional mode"
            )
            return False

        logger.debug(
            f"[ContextCache] Document {document_id} suitable for long context "
            f"({token_count} tokens, max {max_tokens})"
        )
        return True


