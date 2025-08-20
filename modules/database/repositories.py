"""
数据库仓库

提供简单直接的数据访问方法。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, update, delete, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Topic, File, Document, DocumentChunk, FileStatus, TopicStatus

logger = logging.getLogger(__name__)

class BaseRepository:
    """基础仓库类"""
    
    def __init__(self, session: AsyncSession):
        self.session = session

class TopicRepository(BaseRepository):
    """主题仓库"""
    
    async def create_topic(self, name: str, description: str = "", **kwargs) -> Topic:
        """创建主题"""
        topic = Topic(
            name=name,
            description=description,
            status=kwargs.get('status', TopicStatus.ACTIVE),
            category=kwargs.get('category'),
            user_id=kwargs.get('user_id'),
            conversation_id=kwargs.get('conversation_id'),
            parent_topic_id=kwargs.get('parent_topic_id'),
            settings=kwargs.get('settings', {})
        )
        
        self.session.add(topic)
        await self.session.flush()
        await self.session.refresh(topic)
        
        logger.info(f"创建主题: {topic.name} (ID: {topic.id})")
        return topic
    
    async def get_topic_by_id(self, topic_id: int) -> Optional[Topic]:
        """根据ID获取主题"""
        result = await self.session.execute(
            select(Topic)
            .where(Topic.id == topic_id)
            .options(selectinload(Topic.files))
        )
        return result.scalar_one_or_none()
    
    async def get_topics(self, 
                        page: int = 1, 
                        page_size: int = 20,
                        status: Optional[str] = None,
                        user_id: Optional[int] = None) -> List[Topic]:
        """获取主题列表"""
        query = select(Topic)
        
        # 添加过滤条件
        conditions = []
        if status:
            conditions.append(Topic.status == status)
        if user_id:
            conditions.append(Topic.user_id == user_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 添加分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(desc(Topic.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_topic(self, topic_id: int, **updates) -> Optional[Topic]:
        """更新主题"""
        topic = await self.get_topic_by_id(topic_id)
        if not topic:
            return None
        
        for key, value in updates.items():
            if hasattr(topic, key):
                setattr(topic, key, value)
        
        topic.updated_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(topic)
        
        logger.info(f"更新主题: {topic.name} (ID: {topic.id})")
        return topic
    
    async def delete_topic(self, topic_id: int) -> bool:
        """删除主题"""
        result = await self.session.execute(
            delete(Topic).where(Topic.id == topic_id)
        )
        success = result.rowcount > 0
        
        if success:
            logger.info(f"删除主题 ID: {topic_id}")
        
        return success

class FileRepository(BaseRepository):
    """文件仓库"""
    
    async def create_file(self, 
                         file_id: str,
                         original_name: str,
                         content_type: str,
                         file_size: int = 0,
                         **kwargs) -> File:
        """创建文件记录"""
        file_record = File(
            id=file_id,
            original_name=original_name,
            content_type=content_type,
            file_size=file_size,
            file_hash=kwargs.get('file_hash'),
            storage_bucket=kwargs.get('storage_bucket'),
            storage_key=kwargs.get('storage_key'),
            storage_url=kwargs.get('storage_url'),
            status=kwargs.get('status', FileStatus.PENDING),
            topic_id=kwargs.get('topic_id'),
            user_id=kwargs.get('user_id'),
            file_metadata=kwargs.get('metadata', {})
        )
        
        self.session.add(file_record)
        await self.session.flush()
        await self.session.refresh(file_record)
        
        logger.info(f"创建文件记录: {original_name} (ID: {file_id})")
        return file_record
    
    async def get_file_by_id(self, file_id: str) -> Optional[File]:
        """根据ID获取文件"""
        result = await self.session.execute(
            select(File)
            .where(and_(File.id == file_id, File.is_deleted == False))
            .options(selectinload(File.topic))
        )
        return result.scalar_one_or_none()
    
    async def get_files_by_topic(self, 
                               topic_id: int,
                               page: int = 1,
                               page_size: int = 20,
                               status: Optional[str] = None) -> List[File]:
        """获取主题下的文件列表"""
        query = select(File).where(
            and_(
                File.topic_id == topic_id,
                File.is_deleted == False
            )
        )
        
        if status:
            query = query.where(File.status == status)
        
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(desc(File.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_file_status(self, 
                               file_id: str, 
                               status: str,
                               processing_status: Optional[str] = None,
                               error_message: Optional[str] = None) -> Optional[File]:
        """更新文件状态"""
        file_record = await self.get_file_by_id(file_id)
        if not file_record:
            return None
        
        file_record.status = status
        if processing_status is not None:
            file_record.processing_status = processing_status
        if error_message is not None:
            file_record.error_message = error_message
        
        file_record.updated_at = datetime.utcnow()
        await self.session.flush()
        await self.session.refresh(file_record)
        
        logger.info(f"更新文件状态: {file_id} -> {status}")
        return file_record
    
    async def soft_delete_file(self, file_id: str) -> bool:
        """软删除文件"""
        result = await self.session.execute(
            update(File)
            .where(File.id == file_id)
            .values(is_deleted=True, updated_at=datetime.utcnow())
        )
        success = result.rowcount > 0
        
        if success:
            logger.info(f"软删除文件: {file_id}")
        
        return success

class DocumentRepository(BaseRepository):
    """文档仓库"""
    
    async def create_document(self,
                            document_id: str,
                            title: str,
                            content_type: str,
                            **kwargs) -> Document:
        """创建文档"""
        document = Document(
            id=document_id,
            title=title,
            content=kwargs.get('content'),
            content_type=content_type,
            file_id=kwargs.get('file_id'),
            file_path=kwargs.get('file_path'),
            file_size=kwargs.get('file_size', 0),
            status=kwargs.get('status', 'pending'),
            doc_metadata=kwargs.get('metadata', {})
        )
        
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        
        logger.info(f"创建文档: {title} (ID: {document_id})")
        return document
    
    async def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """根据ID获取文档"""
        result = await self.session.execute(
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.chunks))
        )
        return result.scalar_one_or_none()
    
    async def create_document_chunk(self,
                                  document_id: str,
                                  content: str,
                                  chunk_index: int,
                                  **kwargs) -> DocumentChunk:
        """创建文档块"""
        chunk_id = kwargs.get('chunk_id', f"{document_id}_chunk_{chunk_index}")
        
        chunk = DocumentChunk(
            id=chunk_id,
            document_id=document_id,
            content=content,
            chunk_index=chunk_index,
            start_char=kwargs.get('start_char'),
            end_char=kwargs.get('end_char'),
            embedding_vector=kwargs.get('embedding_vector'),
            chunk_metadata=kwargs.get('metadata', {})
        )
        
        self.session.add(chunk)
        await self.session.flush()
        await self.session.refresh(chunk)
        
        logger.info(f"创建文档块: {chunk_id}")
        return chunk
    
    async def search_documents(self,
                             query: str,
                             limit: int = 10,
                             content_type: Optional[str] = None) -> List[Document]:
        """搜索文档（简单文本搜索）"""
        # 这里是简单的文本搜索，生产环境应该使用全文搜索或向量搜索
        search_query = select(Document)
        
        conditions = [
            or_(
                Document.title.ilike(f"%{query}%"),
                Document.content.ilike(f"%{query}%")
            )
        ]
        
        if content_type:
            conditions.append(Document.content_type == content_type)
        
        search_query = search_query.where(and_(*conditions)).limit(limit)
        
        result = await self.session.execute(search_query)
        return result.scalars().all()
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        # 先删除文档块
        await self.session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        
        # 再删除文档
        result = await self.session.execute(
            delete(Document).where(Document.id == document_id)
        )
        
        success = result.rowcount > 0
        if success:
            logger.info(f"删除文档: {document_id}")
        
        return success
