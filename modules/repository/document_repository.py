"""
Document repository implementation

处理文档和文档块相关的数据访问逻辑。
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, desc, or_, select, update
from sqlalchemy.orm import selectinload

from modules.database.models import Document, DocumentChunk
from modules.repository.base_repository import BaseRepository
from modules.repository.interfaces import IDocumentRepository

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository, IDocumentRepository):
    """Document repository implementation"""

    async def create_document(
        self, document_id: str, title: str, content_type: str, **kwargs
    ) -> Document:
        """Create document"""
        document = Document(
            id=document_id,
            title=title,
            content=kwargs.get("content"),
            content_type=content_type,
            file_id=kwargs.get("file_id"),
            file_path=kwargs.get("file_path"),
            file_size=kwargs.get("file_size", 0),
            status=kwargs.get("status", "pending"),
            doc_metadata=kwargs.get("metadata", {}),
        )

        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)

        logger.info(f"Create document: {title} (ID: {document_id})")
        return document

    async def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """根据IDGet document"""
        result = await self.session.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.chunks))
        )
        return result.scalar_one_or_none()

    async def create_document_chunk(
        self, document_id: str, content: str, chunk_index: int, **kwargs
    ) -> DocumentChunk:
        """Create document块"""
        chunk_id = kwargs.get("chunk_id", f"{document_id}_chunk_{chunk_index}")

        chunk = DocumentChunk(
            id=chunk_id,
            document_id=document_id,
            content=content,
            chunk_index=chunk_index,
            start_char=kwargs.get("start_char"),
            end_char=kwargs.get("end_char"),
            embedding_vector=kwargs.get("embedding_vector"),
            chunk_metadata=kwargs.get("metadata", {}),
        )

        self.session.add(chunk)
        await self.session.flush()
        await self.session.refresh(chunk)

        logger.info(f"Create document块: {chunk_id}")
        return chunk

    async def search_documents(
        self, query: str, limit: int = 10, content_type: Optional[str] = None
    ) -> List[Document]:
        """搜索文档"""
        search_query = select(Document)

        conditions = [
            or_(
                Document.title.ilike(f"%{query}%"), Document.content.ilike(f"%{query}%")
            )
        ]

        if content_type:
            conditions.append(Document.content_type == content_type)

        search_query = search_query.where(and_(*conditions)).limit(limit)

        result = await self.session.execute(search_query)
        return result.scalars().all()

    async def delete_document(self, document_id: str) -> bool:
        """Delete document"""
        # 先Delete document块
        await self.session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )

        # 再Delete document
        result = await self.session.execute(
            delete(Document).where(Document.id == document_id)
        )

        success = result.rowcount > 0
        if success:
            logger.info(f"Delete document: {document_id}")

        return success

    async def get_documents_by_file(self, file_id: str) -> List[Document]:
        """根据文件IDGet document列表"""
        result = await self.session.execute(
            select(Document)
            .where(Document.file_id == file_id)
            .order_by(desc(Document.created_at))
        )
        return result.scalars().all()

    async def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        """Get document的所有块"""
        result = await self.session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return result.scalars().all()

    async def update_document_status(self, document_id: str, status: str) -> bool:
        """Update document状态"""
        result = await self.session.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(status=status, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    async def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """Update document metadata"""
        try:
            document = await self.get_document_by_id(document_id)
            if document:
                # 合并现有元数据和新元数据
                current_metadata = document.doc_metadata or {}
                current_metadata.update(metadata)
                
                result = await self.session.execute(
                    update(Document)
                    .where(Document.id == document_id)
                    .values(doc_metadata=current_metadata, updated_at=datetime.now(timezone.utc))
                )
                return result.rowcount > 0
            return False
        except Exception as e:
            logger.error(f"Failed to update document metadata: {e}")
            return False

    # 实现基类抽象方法
    async def create(self, entity_data: Dict[str, Any]) -> Document:
        return await self.create_document(**entity_data)

    async def get_by_id(self, entity_id: str) -> Optional[Document]:
        return await self.get_document_by_id(entity_id)

    async def update(
        self, entity_id: str, updates: Dict[str, Any]
    ) -> Optional[Document]:
        document = await self.get_document_by_id(entity_id)
        if not document:
            return None

        for key, value in updates.items():
            if hasattr(document, key):
                setattr(document, key, value)

        document.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(document)

        return document

    async def delete(self, entity_id: str) -> bool:
        return await self.delete_document(entity_id)

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[Document]:
        query = select(Document)

        if filters:
            if "content_type" in filters:
                query = query.where(Document.content_type == filters["content_type"])
            if "status" in filters:
                query = query.where(Document.status == filters["status"])
            if "file_id" in filters:
                query = query.where(Document.file_id == filters["file_id"])

        offset = (page - 1) * page_size
        query = (
            query.offset(offset).limit(page_size).order_by(desc(Document.created_at))
        )

        result = await self.session.execute(query)
        return result.scalars().all()
