"""
SQLAlchemy document repository implementation.

Implements the DocumentRepository interface using SQLAlchemy ORM.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from ...core.entities.document import Document
from ...core.repositories.document_repository import DocumentRepository
from ...core.value_objects.document_chunk import DocumentChunk


class SqlAlchemyDocumentRepository(DocumentRepository):
    """SQLAlchemy implementation of DocumentRepository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def save(self, document: Document) -> None:
        """Save a document."""
        # Import here to avoid circular imports
        from modules.database.models import Document as DocumentModel
        
        # Check if document exists
        stmt = select(DocumentModel).where(DocumentModel.id == document.id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing document
            existing.title = document.title
            existing.content = document.content
            existing.content_type = document.content_type
            existing.file_id = document.file_id
            existing.file_path = document.file_path
            existing.file_size = document.file_size
            existing.status = document.status
            existing.processing_status = document.processing_status
            existing.doc_metadata = document.metadata
            existing.updated_at = document.updated_at
        else:
            # Create new document
            document_model = DocumentModel(
                id=document.id,
                title=document.title,
                content=document.content,
                content_type=document.content_type,
                file_id=document.file_id,
                file_path=document.file_path,
                file_size=document.file_size,
                status=document.status,
                processing_status=document.processing_status,
                doc_metadata=document.metadata,
                created_at=document.created_at,
                updated_at=document.updated_at
            )
            self._session.add(document_model)
        
        await self._session.commit()
    
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        from modules.database.models import Document as DocumentModel
        
        stmt = select(DocumentModel).where(DocumentModel.id == document_id)
        result = await self._session.execute(stmt)
        document_model = result.scalar_one_or_none()
        
        if not document_model:
            return None
        
        return self._model_to_entity(document_model)
    
    async def get_by_file_id(self, file_id: str) -> List[Document]:
        """Get documents by file ID."""
        from modules.database.models import Document as DocumentModel
        
        stmt = select(DocumentModel).where(DocumentModel.file_id == file_id)
        result = await self._session.execute(stmt)
        document_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in document_models]
    
    async def search(self, query: str, limit: int = 10) -> List[Document]:
        """Search documents by content."""
        from modules.database.models import Document as DocumentModel
        
        stmt = (
            select(DocumentModel)
            .where(
                DocumentModel.content.contains(query) | 
                DocumentModel.title.contains(query)
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        document_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in document_models]
    
    async def list_by_status(self, status: str, limit: int = 100) -> List[Document]:
        """List documents by status."""
        from modules.database.models import Document as DocumentModel
        
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.status == status)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        document_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in document_models]
    
    async def update_status(self, document_id: str, status: str, processing_status: Optional[str] = None) -> bool:
        """Update document status."""
        from modules.database.models import Document as DocumentModel
        
        update_data = {"status": status}
        if processing_status:
            update_data["processing_status"] = processing_status
        
        stmt = (
            update(DocumentModel)
            .where(DocumentModel.id == document_id)
            .values(**update_data)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        
        return result.rowcount > 0
    
    async def delete(self, document_id: str) -> bool:
        """Delete a document."""
        from modules.database.models import Document as DocumentModel
        
        stmt = delete(DocumentModel).where(DocumentModel.id == document_id)
        result = await self._session.execute(stmt)
        await self._session.commit()
        
        return result.rowcount > 0
    
    async def count_by_status(self, status: str) -> int:
        """Count documents by status."""
        from modules.database.models import Document as DocumentModel
        
        stmt = select(func.count(DocumentModel.id)).where(DocumentModel.status == status)
        result = await self._session.execute(stmt)
        return result.scalar() or 0
    
    # Document chunk operations
    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Save document chunks."""
        from modules.database.models import DocumentChunk as ChunkModel
        
        for chunk in chunks:
            # Check if chunk exists
            stmt = select(ChunkModel).where(ChunkModel.id == chunk.id)
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing chunk
                existing.content = chunk.content
                existing.chunk_index = chunk.chunk_index
                existing.start_char = chunk.start_char
                existing.end_char = chunk.end_char
                existing.embedding_vector = chunk.embedding_vector
                existing.chunk_metadata = chunk.metadata or {}
            else:
                # Create new chunk
                chunk_model = ChunkModel(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    embedding_vector=chunk.embedding_vector,
                    chunk_metadata=chunk.metadata or {}
                )
                self._session.add(chunk_model)
        
        await self._session.commit()
    
    async def get_chunks_by_document_id(self, document_id: str) -> List[DocumentChunk]:
        """Get chunks for a document."""
        from modules.database.models import DocumentChunk as ChunkModel
        
        stmt = (
            select(ChunkModel)
            .where(ChunkModel.document_id == document_id)
            .order_by(ChunkModel.chunk_index)
        )
        result = await self._session.execute(stmt)
        chunk_models = result.scalars().all()
        
        return [self._chunk_model_to_value_object(model) for model in chunk_models]
    
    async def delete_chunks_by_document_id(self, document_id: str) -> bool:
        """Delete all chunks for a document."""
        from modules.database.models import DocumentChunk as ChunkModel
        
        stmt = delete(ChunkModel).where(ChunkModel.document_id == document_id)
        result = await self._session.execute(stmt)
        await self._session.commit()
        
        return result.rowcount > 0
    
    async def search_chunks(self, query: str, limit: int = 10) -> List[DocumentChunk]:
        """Search document chunks."""
        from modules.database.models import DocumentChunk as ChunkModel
        
        stmt = (
            select(ChunkModel)
            .where(ChunkModel.content.contains(query))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        chunk_models = result.scalars().all()
        
        return [self._chunk_model_to_value_object(model) for model in chunk_models]
    
    def _model_to_entity(self, model) -> Document:
        """Convert SQLAlchemy model to Document entity."""
        return Document(
            id=model.id,
            title=model.title,
            content=model.content,
            content_type=model.content_type,
            file_id=model.file_id,
            file_path=model.file_path,
            file_size=model.file_size,
            status=model.status,
            processing_status=model.processing_status,
            metadata=model.doc_metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _chunk_model_to_value_object(self, model) -> DocumentChunk:
        """Convert SQLAlchemy chunk model to DocumentChunk value object."""
        return DocumentChunk(
            id=model.id,
            document_id=model.document_id,
            content=model.content,
            chunk_index=model.chunk_index,
            start_char=model.start_char,
            end_char=model.end_char,
            metadata=model.chunk_metadata or {},
            embedding_vector=model.embedding_vector
        )