"""
文档Service层

处理文档相关的业务逻辑。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .base_service import BaseService
from ..repository import DocumentRepository, FileRepository
from ..schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentList,
    DocumentChunkCreate, DocumentChunkResponse,
    ProcessingRequest, ProcessingResult, SearchRequest, SearchResponse,
    document_to_response, documents_to_responses, ProcessingStatus
)

logger = logging.getLogger(__name__)

class DocumentService(BaseService):
    """文档业务服务"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.document_repo = DocumentRepository(session)
        self.file_repo = FileRepository(session)
    
    async def create_document(self, document_data: DocumentCreate) -> DocumentResponse:
        """创建文档"""
        try:
            # 验证文档创建
            await self._validate_document_creation(document_data)
            
            # 创建文档
            document = await self.document_repo.create_document(
                document_id=document_data.id,
                title=document_data.title,
                content=document_data.content,
                content_type=document_data.content_type,
                file_id=document_data.file_id,
                file_path=document_data.file_path,
                file_size=document_data.file_size,
                metadata=document_data.doc_metadata
            )
            
            self.logger.info(f"Created document: {document.title} (ID: {document.id})")
            return document_to_response(document)
            
        except Exception as e:
            self._handle_error(e, "create_document")
    
    async def get_document(self, document_id: str) -> Optional[DocumentResponse]:
        """获取文档详情"""
        try:
            document = await self.document_repo.get_document_by_id(document_id)
            if not document:
                return None
            
            # 获取文档块数量
            chunks = await self.document_repo.get_document_chunks(document_id)
            chunk_count = len(chunks)
            
            return document_to_response(document, chunk_count=chunk_count)
            
        except Exception as e:
            self._handle_error(e, f"get_document_{document_id}")
    
    async def update_document(self, document_id: str, document_data: DocumentUpdate) -> Optional[DocumentResponse]:
        """更新文档"""
        try:
            # 检查文档是否存在
            existing_document = await self.document_repo.get_document_by_id(document_id)
            if not existing_document:
                return None
            
            # 准备更新字典
            update_dict = document_data.model_dump(exclude_none=True)
            
            # 更新文档
            updated_document = await self.document_repo.update(document_id, update_dict)
            
            self.logger.info(f"Updated document: {document_id}")
            return document_to_response(updated_document) if updated_document else None
            
        except Exception as e:
            self._handle_error(e, f"update_document_{document_id}")
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            # 删除文档（会级联删除文档块）
            success = await self.document_repo.delete_document(document_id)
            
            if success:
                self.logger.info(f"Deleted document: {document_id}")
            
            return success
            
        except Exception as e:
            self._handle_error(e, f"delete_document_{document_id}")
    
    async def list_documents(self, 
                           page: int = 1, 
                           page_size: int = 20,
                           content_type: Optional[str] = None,
                           status: Optional[str] = None,
                           file_id: Optional[str] = None) -> DocumentList:
        """获取文档列表"""
        try:
            # 构建过滤条件
            filters = {}
            if content_type:
                filters['content_type'] = content_type
            if status:
                filters['status'] = status
            if file_id:
                filters['file_id'] = file_id
            
            # 获取文档列表
            documents = await self.document_repo.list(
                page=page,
                page_size=page_size,
                filters=filters
            )
            
            # 获取总数
            all_documents = await self.document_repo.list(page=1, page_size=1000, filters=filters)
            total = len(all_documents)
            total_pages = (total + page_size - 1) // page_size
            
            # 转换为响应Schema
            document_responses = documents_to_responses(documents)
            
            return DocumentList(
                documents=document_responses,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            self._handle_error(e, "list_documents")
    
    async def process_document(self, request: ProcessingRequest) -> ProcessingResult:
        """处理文档（分块和向量化）"""
        try:
            start_time = datetime.utcnow()
            
            # 获取文档
            document = await self.document_repo.get_document_by_id(request.document_id)
            if not document:
                raise ValueError(f"文档 {request.document_id} 不存在")
            
            # 更新文档状态为处理中
            await self.document_repo.update_document_status(request.document_id, "processing")
            
            # 执行文档分块
            chunks_created = await self._chunk_document(document, request)
            
            # 更新文档状态为已完成
            await self.document_repo.update_document_status(request.document_id, "processed")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(f"Processed document {request.document_id}: {chunks_created} chunks created")
            
            return ProcessingResult(
                document_id=request.document_id,
                status=ProcessingStatus.COMPLETED,
                chunks_created=chunks_created,
                processing_time=processing_time,
                metadata={
                    'chunking_strategy': request.chunking_strategy,
                    'chunk_size': request.chunk_size,
                    'chunk_overlap': request.chunk_overlap
                }
            )
            
        except Exception as e:
            # 更新文档状态为失败
            await self.document_repo.update_document_status(request.document_id, "failed")
            
            return ProcessingResult(
                document_id=request.document_id,
                status=ProcessingStatus.FAILED,
                chunks_created=0,
                error_message=str(e)
            )
    
    async def search_documents(self, request: SearchRequest) -> SearchResponse:
        """搜索文档"""
        try:
            start_time = datetime.utcnow()
            
            # 执行搜索
            documents = await self.document_repo.search_documents(
                query=request.query,
                limit=request.limit,
                content_type=request.content_type
            )
            
            # 构建搜索结果
            from ..schemas.responses import SearchResult
            results = []
            for doc in documents:
                results.append(SearchResult(
                    document_id=doc.id,
                    title=doc.title,
                    content=doc.content[:500] if doc.content else "",  # 截取前500字符
                    score=0.8,  # 简化评分
                    content_type=doc.content_type,
                    file_id=doc.file_id,
                    metadata=doc.doc_metadata or {}
                ))
            
            search_time = (datetime.utcnow() - start_time).total_seconds()
            
            return SearchResponse(
                query=request.query,
                results=results,
                total_results=len(results),
                search_time=search_time,
                search_type=request.search_type
            )
            
        except Exception as e:
            self._handle_error(e, f"search_documents_{request.query}")
    
    async def get_file_documents(self, file_id: str) -> List[DocumentResponse]:
        """获取文件的文档列表"""
        try:
            documents = await self.document_repo.get_documents_by_file(file_id)
            return documents_to_responses(documents)
            
        except Exception as e:
            self._handle_error(e, f"get_file_documents_{file_id}")
    
    async def get_document_chunks(self, document_id: str) -> List[DocumentChunkResponse]:
        """获取文档的所有块"""
        try:
            chunks = await self.document_repo.get_document_chunks(document_id)
            
            # 转换为响应Schema
            from ..schemas.document import DocumentChunkResponse
            chunk_responses = []
            for chunk in chunks:
                chunk_responses.append(DocumentChunkResponse(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    embedding_vector=chunk.embedding_vector,
                    chunk_metadata=chunk.chunk_metadata or {},
                    created_at=chunk.created_at,
                    updated_at=chunk.updated_at
                ))
            
            return chunk_responses
            
        except Exception as e:
            self._handle_error(e, f"get_document_chunks_{document_id}")
    
    # 私有方法
    async def _validate_document_creation(self, document_data: DocumentCreate) -> None:
        """验证文档创建"""
        # 检查文件是否存在
        if document_data.file_id:
            file_record = await self.file_repo.get_file_by_id(document_data.file_id)
            if not file_record:
                raise ValueError(f"文件 {document_data.file_id} 不存在")
    
    async def _chunk_document(self, document, request: ProcessingRequest) -> int:
        """文档分块处理"""
        if not document.content:
            return 0
        
        # 简化的固定大小分块
        content = document.content
        chunk_size = request.chunk_size
        chunk_overlap = request.chunk_overlap
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk_content = content[start:end]
            
            # 创建文档块
            await self.document_repo.create_document_chunk(
                document_id=document.id,
                content=chunk_content,
                chunk_index=chunk_index,
                start_char=start,
                end_char=end
            )
            
            chunks.append(chunk_content)
            start = end - chunk_overlap
            chunk_index += 1
            
            if start >= len(content):
                break
        
        return len(chunks)
