"""
Knowledge Orchestration Services

知识管理业务编排服务，负责：
1. 协调不同Domain Services
2. 管理业务流程和事务
3. 处理跨聚合的操作
4. 实现复杂的业务用例

不包含具体的技术实现，只负责业务逻辑的编排。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

# Domain imports
from domain.knowledge import (
    DocumentId, ChunkId, KnowledgeDocument, DocumentChunk,
    SearchQuery, SearchResult, ProcessingStatus, ChunkingStrategy,
    IKnowledgeRepository, IDocumentProcessor, IVectorService, 
    ISearchService, IKnowledgeManagementService,
    DocumentIngested, DocumentProcessed, DocumentProcessingFailed
)

# Application DTOs
from application.dtos.knowledge import (
    DocumentIngestionRequest, DocumentIngestionResponse,
    DocumentProcessingRequest, DocumentProcessingResponse,
    SearchRequest, SearchResponse,
    DocumentListRequest, DocumentListResponse
)

# Event bus
from application.event.event_bus import EventBus

logger = logging.getLogger(__name__)


class KnowledgeOrchestrationService:
    """
    知识管理编排服务
    
    负责协调各种领域服务，实现复杂的业务流程。
    这是Application Layer的核心服务，连接Domain和Infrastructure。
    """
    
    def __init__(self,
                 knowledge_repository: IKnowledgeRepository,
                 document_processor: IDocumentProcessor,
                 vector_service: IVectorService,
                 search_service: ISearchService,
                 event_bus: EventBus):
        """
        初始化编排服务
        
        Args:
            knowledge_repository: 知识仓储接口
            document_processor: 文档处理器接口  
            vector_service: 向量服务接口
            search_service: 搜索服务接口
            event_bus: 事件总线
        """
        self.knowledge_repository = knowledge_repository
        self.document_processor = document_processor
        self.vector_service = vector_service
        self.search_service = search_service
        self.event_bus = event_bus
    
    async def ingest_document(self, request: DocumentIngestionRequest) -> DocumentIngestionResponse:
        """
        文档摄取业务流程编排
        
        这是一个复杂的业务流程，包含多个步骤：
        1. 创建文档实体
        2. 保存到仓储
        3. 发布事件
        4. 可选择立即处理或异步处理
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting document ingestion for: {request.source_location}")
            
            # 1. 创建文档实体
            document_id = DocumentId(f"doc_{hash(request.source_location)}_{int(start_time.timestamp())}")
            
            document = KnowledgeDocument(
                id=document_id,
                title=request.title or f"Document from {request.source_location}",
                content="",  # 初始为空，待处理时填充
                content_type=request.content_type,
                source_location=request.source_location,
                status=ProcessingStatus.PENDING,
                created_at=start_time,
                updated_at=start_time,
                metadata=request.metadata or {}
            )
            
            # 2. 保存到仓储
            await self.knowledge_repository.save_document(document)
            
            # 3. 发布文档摄取事件
            ingestion_event = DocumentIngested(
                document_id=document_id,
                source_location=request.source_location,
                occurred_at=start_time
            )
            await self.event_bus.publish(ingestion_event)
            
            # 4. 如果要求立即处理，则启动处理流程
            if request.process_immediately:
                # 异步启动处理，不等待完成
                asyncio.create_task(self._process_document_async(document_id))
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return DocumentIngestionResponse(
                success=True,
                document_id=document_id.value,
                status=ProcessingStatus.PENDING,
                message=f"Document ingested successfully: {document.title}",
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to ingest document: {e}")
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return DocumentIngestionResponse(
                success=False,
                status=ProcessingStatus.FAILED,
                message=f"Failed to ingest document: {str(e)}",
                errors=[str(e)],
                processing_time_ms=processing_time
            )
    
    async def process_document(self, request: DocumentProcessingRequest) -> DocumentProcessingResponse:
        """
        文档处理业务流程编排
        
        完整的文档处理流程：
        1. 加载文档
        2. 提取内容
        3. 文档分块
        4. 生成向量
        5. 存储向量
        6. 更新状态
        7. 发布事件
        """
        start_time = datetime.utcnow()
        document_id = DocumentId(request.document_id)
        
        try:
            logger.info(f"Starting document processing for: {document_id.value}")
            
            # 1. 加载文档
            document = await self.knowledge_repository.find_document_by_id(document_id)
            if not document:
                raise ValueError(f"Document not found: {document_id.value}")
            
            # 2. 标记为处理中
            document.mark_as_processing()
            await self.knowledge_repository.save_document(document)
            
            # 3. 提取内容
            content = await self.document_processor.extract_content(
                document.source_location, 
                document.content_type
            )
            document.content = content
            
            # 4. 验证文档
            is_valid = await self.document_processor.validate_document(document)
            if not is_valid:
                raise ValueError("Document validation failed")
            
            # 5. 文档分块
            chunks = await self.document_processor.chunk_document(
                document, 
                request.chunking_strategy or ChunkingStrategy.FIXED_SIZE,
                request.chunk_size or 1000,
                request.chunk_overlap or 200
            )
            
            # 6. 生成向量
            if request.generate_embeddings:
                chunk_texts = [chunk.content for chunk in chunks]
                embeddings = await self.vector_service.generate_embeddings(chunk_texts)
                
                # 更新块的向量
                for chunk, embedding in zip(chunks, embeddings):
                    chunk.embedding_vector = embedding
                
                # 7. 存储向量
                await self.vector_service.store_vectors(chunks)
            
            # 8. 保存块到仓储
            await self.knowledge_repository.save_chunks(chunks)
            
            # 9. 标记为完成
            document.mark_as_completed()
            await self.knowledge_repository.save_document(document)
            
            # 10. 发布处理完成事件
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            processed_event = DocumentProcessed(
                document_id=document_id,
                chunk_count=len(chunks),
                processing_time_ms=processing_time,
                occurred_at=datetime.utcnow()
            )
            await self.event_bus.publish(processed_event)
            
            return DocumentProcessingResponse(
                success=True,
                document_id=document_id.value,
                status=ProcessingStatus.COMPLETED,
                message=f"Document processed successfully: {len(chunks)} chunks created",
                chunks_created=len(chunks),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id.value}: {e}")
            
            # 标记为失败
            try:
                document = await self.knowledge_repository.find_document_by_id(document_id)
                if document:
                    document.mark_as_failed(str(e))
                    await self.knowledge_repository.save_document(document)
                    
                    # 发布失败事件
                    failed_event = DocumentProcessingFailed(
                        document_id=document_id,
                        error_message=str(e),
                        occurred_at=datetime.utcnow()
                    )
                    await self.event_bus.publish(failed_event)
            except Exception as update_error:
                logger.error(f"Failed to update document status: {update_error}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return DocumentProcessingResponse(
                success=False,
                document_id=document_id.value,
                status=ProcessingStatus.FAILED,
                message=f"Failed to process document: {str(e)}",
                errors=[str(e)],
                processing_time_ms=processing_time
            )
    
    async def search_knowledge(self, request: SearchRequest) -> SearchResponse:
        """
        知识搜索业务流程编排
        
        协调不同的搜索策略和结果合并。
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Performing knowledge search: {request.query_text}")
            
            # 构建搜索查询对象
            search_query = SearchQuery(
                text=request.query_text,
                strategy=request.strategy,
                max_results=request.max_results,
                filters=request.filters or {}
            )
            
            # 执行搜索
            results = await self.search_service.search(search_query)
            
            search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SearchResponse(
                success=True,
                query=request.query_text,
                strategy=request.strategy.value,
                results=results,
                total_found=len(results),
                search_time_ms=search_time
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return SearchResponse(
                success=False,
                query=request.query_text,
                strategy=request.strategy.value,
                results=[],
                total_found=0,
                search_time_ms=search_time,
                errors=[str(e)]
            )
    
    async def list_documents(self, request: DocumentListRequest) -> DocumentListResponse:
        """
        文档列表查询业务流程编排
        """
        try:
            # 根据状态筛选
            if request.status_filter:
                documents = await self.knowledge_repository.find_documents_by_status(
                    request.status_filter
                )
            else:
                # TODO: 实现更复杂的查询逻辑
                documents = await self.knowledge_repository.find_documents_by_status(
                    ProcessingStatus.COMPLETED
                )
            
            # 应用分页
            start_idx = request.offset or 0
            end_idx = start_idx + (request.limit or 50)
            paged_documents = documents[start_idx:end_idx]
            
            return DocumentListResponse(
                success=True,
                documents=paged_documents,
                total_count=len(documents),
                limit=request.limit or 50,
                offset=request.offset or 0
            )
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return DocumentListResponse(
                success=False,
                documents=[],
                total_count=0,
                errors=[str(e)]
            )
    
    async def _process_document_async(self, document_id: DocumentId) -> None:
        """
        异步处理文档的私有方法
        """
        try:
            processing_request = DocumentProcessingRequest(
                document_id=document_id.value,
                generate_embeddings=True,
                chunking_strategy=ChunkingStrategy.FIXED_SIZE
            )
            await self.process_document(processing_request)
        except Exception as e:
            logger.error(f"Async document processing failed for {document_id.value}: {e}")


class KnowledgeWorkflowService:
    """
    知识管理工作流服务
    
    负责更高层次的业务工作流，如批量处理、数据迁移等。
    """
    
    def __init__(self, orchestration_service: KnowledgeOrchestrationService):
        self.orchestration_service = orchestration_service
    
    async def batch_ingest_documents(self, 
                                   requests: List[DocumentIngestionRequest],
                                   max_concurrent: int = 5) -> List[DocumentIngestionResponse]:
        """
        批量文档摄取工作流
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single(request: DocumentIngestionRequest) -> DocumentIngestionResponse:
            async with semaphore:
                return await self.orchestration_service.ingest_document(request)
        
        tasks = [process_single(request) for request in requests]
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    async def bulk_process_pending_documents(self, batch_size: int = 10) -> Dict[str, int]:
        """
        批量处理待处理文档的工作流
        """
        pending_documents = await self.orchestration_service.knowledge_repository.find_documents_by_status(
            ProcessingStatus.PENDING
        )
        
        processed_count = 0
        failed_count = 0
        
        # 分批处理
        for i in range(0, len(pending_documents), batch_size):
            batch = pending_documents[i:i + batch_size]
            
            tasks = []
            for document in batch:
                processing_request = DocumentProcessingRequest(
                    document_id=document.id.value,
                    generate_embeddings=True
                )
                task = self.orchestration_service.process_document(processing_request)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    failed_count += 1
                    logger.error(f"Batch processing failed: {result}")
                elif result.success:
                    processed_count += 1
                else:
                    failed_count += 1
        
        return {
            "total_documents": len(pending_documents),
            "processed_successfully": processed_count,
            "failed": failed_count
        }