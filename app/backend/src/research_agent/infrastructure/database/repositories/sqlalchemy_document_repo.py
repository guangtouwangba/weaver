"""SQLAlchemy implementation of DocumentRepository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from research_agent.domain.entities.document import Document, DocumentStatus
from research_agent.domain.repositories.document_repo import DocumentRepository
from research_agent.infrastructure.database.models import DocumentModel


class SQLAlchemyDocumentRepository(DocumentRepository):
    """SQLAlchemy implementation of document repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, document: Document) -> Document:
        """Save a document."""
        # Check if exists
        existing = await self._session.get(DocumentModel, document.id)

        if existing:
            # Update existing
            existing.filename = document.filename
            existing.original_filename = document.original_filename
            existing.file_path = document.file_path
            existing.file_size = document.file_size
            existing.mime_type = document.mime_type
            existing.page_count = document.page_count
            existing.status = document.status.value
            existing.summary = document.summary
            existing.full_content = document.full_content
            existing.content_token_count = document.content_token_count
            existing.parsing_metadata = document.parsing_metadata
            existing.thumbnail_path = document.thumbnail_path
            existing.thumbnail_status = document.thumbnail_status
        else:
            # Create new
            model = self._to_model(document)
            self._session.add(model)

        await self._session.flush()
        return document

    async def find_by_id(self, document_id: UUID) -> Optional[Document]:
        """Find document by ID."""
        model = await self._session.get(DocumentModel, document_id)
        return self._to_entity(model) if model else None

    async def find_by_project(self, project_id: UUID) -> List[Document]:
        """Find all documents for a project."""
        result = await self._session.execute(
            select(DocumentModel)
            .where(DocumentModel.project_id == project_id)
            .order_by(DocumentModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def delete(self, document_id: UUID) -> bool:
        """Delete a document."""
        model = await self._session.get(DocumentModel, document_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()
            return True
        return False

    def _to_model(self, entity: Document) -> DocumentModel:
        """Convert entity to ORM model."""
        return DocumentModel(
            id=entity.id,
            project_id=entity.project_id,
            filename=entity.filename,
            original_filename=entity.original_filename,
            file_path=entity.file_path,
            file_size=entity.file_size,
            mime_type=entity.mime_type,
            page_count=entity.page_count,
            status=entity.status.value,
            summary=entity.summary,
            full_content=entity.full_content,
            content_token_count=entity.content_token_count,
            parsing_metadata=entity.parsing_metadata,
            thumbnail_path=entity.thumbnail_path,
            thumbnail_status=entity.thumbnail_status,
            created_at=entity.created_at,
        )

    def _to_entity(self, model: DocumentModel) -> Document:
        """Convert ORM model to entity."""
        return Document(
            id=model.id,
            project_id=model.project_id,
            filename=model.filename,
            original_filename=model.original_filename,
            file_path=model.file_path,
            file_size=model.file_size or 0,
            mime_type=model.mime_type,
            page_count=model.page_count or 0,
            status=DocumentStatus(model.status),
            summary=model.summary,
            full_content=model.full_content,
            content_token_count=model.content_token_count,
            parsing_metadata=model.parsing_metadata,
            thumbnail_path=model.thumbnail_path,
            thumbnail_status=model.thumbnail_status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
