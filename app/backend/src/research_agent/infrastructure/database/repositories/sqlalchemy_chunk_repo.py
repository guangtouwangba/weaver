"""SQLAlchemy implementation of ChunkRepository."""

from typing import List
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.chunk import DocumentChunk
from research_agent.domain.repositories.chunk_repo import ChunkRepository
from research_agent.infrastructure.database.models import DocumentChunkModel


class SQLAlchemyChunkRepository(ChunkRepository):
    """SQLAlchemy implementation of chunk repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_batch(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Save multiple chunks."""
        models = [self._to_model(chunk) for chunk in chunks]
        self._session.add_all(models)
        await self._session.flush()
        return chunks

    async def find_by_document(self, document_id: UUID) -> List[DocumentChunk]:
        """Find all chunks for a document."""
        result = await self._session.execute(
            select(DocumentChunkModel)
            .where(DocumentChunkModel.document_id == document_id)
            .order_by(DocumentChunkModel.chunk_index)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all chunks for a document."""
        result = await self._session.execute(
            delete(DocumentChunkModel).where(DocumentChunkModel.document_id == document_id)
        )
        await self._session.flush()
        return result.rowcount

    def _to_model(self, entity: DocumentChunk) -> DocumentChunkModel:
        """Convert entity to ORM model."""
        return DocumentChunkModel(
            id=entity.id,
            document_id=entity.document_id,
            project_id=entity.project_id,
            chunk_index=entity.chunk_index,
            content=entity.content,
            page_number=entity.page_number,
            embedding=entity.embedding,
            chunk_metadata=entity.metadata,
            created_at=entity.created_at,
        )

    def _to_entity(self, model: DocumentChunkModel) -> DocumentChunk:
        """Convert ORM model to entity."""
        return DocumentChunk(
            id=model.id,
            document_id=model.document_id,
            project_id=model.project_id,
            chunk_index=model.chunk_index,
            content=model.content,
            page_number=model.page_number or 0,
            embedding=list(model.embedding) if model.embedding else None,
            metadata=model.chunk_metadata,
            created_at=model.created_at,
        )

