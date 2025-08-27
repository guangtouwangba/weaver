"""
文档Service层

处理文档相关的Business logic。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from modules.file_loader import FileLoaderFactory
from modules.embedding import EmbeddingProvider
# RAG pipeline imports will be imported dynamically to avoid circular import
from modules.pipeline import (
    DocumentProcessingRequest,
    PipelineStatus,
)
from modules.processors import ChunkingProcessor
from modules.vector_store import VectorStoreProvider
from modules.repository import DocumentRepository, FileRepository
from modules.schemas import (
    ContentType,
    DocumentChunkResponse,
    DocumentCreate,
    DocumentList,
    DocumentResponse,
    DocumentUpdate,
    ProcessingRequest,
    ProcessingResult,
    ProcessingStatus,
    SearchRequest,
    SearchResponse,
    document_to_response,
    documents_to_responses,
)
from modules.services.base_service import BaseService

logger = logging.getLogger(__name__)


class DocumentService(BaseService):
    """Document business service"""

    def __init__(self, session: AsyncSession, enable_rag: bool = True):
        super().__init__(session)
        self.document_repo = DocumentRepository(session)
        self.file_repo = FileRepository(session)

        # RAG pipeline components
        self.enable_rag = enable_rag
        self._rag_pipeline = None
        self._rag_initialized = False

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
                metadata=document_data.doc_metadata,
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

    async def update_document(
        self, document_id: str, document_data: DocumentUpdate
    ) -> Optional[DocumentResponse]:
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

    async def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        content_type: Optional[str] = None,
        status: Optional[str] = None,
        file_id: Optional[str] = None,
    ) -> DocumentList:
        """获取文档列表"""
        try:
            # 构建过滤条件
            filters = {}
            if content_type:
                filters["content_type"] = content_type
            if status:
                filters["status"] = status
            if file_id:
                filters["file_id"] = file_id

            # 获取文档列表
            documents = await self.document_repo.list(
                page=page, page_size=page_size, filters=filters
            )

            # 获取总数
            all_documents = await self.document_repo.list(
                page=1, page_size=1000, filters=filters
            )
            total = len(all_documents)
            total_pages = (total + page_size - 1) // page_size

            # 转换为响应Schema
            document_responses = documents_to_responses(documents)

            return DocumentList(
                documents=document_responses,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
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
            await self.document_repo.update_document_status(
                request.document_id, "processing"
            )

            # 执行文档分块
            chunks_created = await self._chunk_document(document, request)

            # 更新文档状态为已完成
            await self.document_repo.update_document_status(
                request.document_id, "processed"
            )

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            self.logger.info(
                f"Processed document {request.document_id}: {chunks_created} chunks created"
            )

            return ProcessingResult(
                document_id=request.document_id,
                status=ProcessingStatus.COMPLETED,
                chunks_created=chunks_created,
                processing_time=processing_time,
                metadata={
                    "chunking_strategy": request.chunking_strategy,
                    "chunk_size": request.chunk_size,
                    "chunk_overlap": request.chunk_overlap,
                },
            )

        except Exception as e:
            # 更新文档状态为失败
            await self.document_repo.update_document_status(
                request.document_id, "failed"
            )

            return ProcessingResult(
                document_id=request.document_id,
                status=ProcessingStatus.FAILED,
                chunks_created=0,
                error_message=str(e),
            )

    async def search_documents(self, request: SearchRequest) -> SearchResponse:
        """搜索文档"""
        try:
            start_time = datetime.utcnow()

            # 执行搜索
            documents = await self.document_repo.search_documents(
                query=request.query,
                limit=request.limit,
                content_type=request.content_type,
            )

            # 构建搜索结果
            from modules.schemas.responses import SearchResult

            results = []
            for doc in documents:
                results.append(
                    SearchResult(
                        document_id=doc.id,
                        title=doc.title,
                        content=(
                            doc.content[:500] if doc.content else ""
                        ),  # 截取前500字符
                        score=0.8,  # 简化评分
                        content_type=doc.content_type,
                        file_id=doc.file_id,
                        metadata=doc.doc_metadata or {},
                    )
                )

            search_time = (datetime.utcnow() - start_time).total_seconds()

            return SearchResponse(
                query=request.query,
                results=results,
                total_results=len(results),
                search_time=search_time,
                search_type=request.search_type,
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

    async def get_document_chunks(
        self, document_id: str
    ) -> List[DocumentChunkResponse]:
        """获取文档的所有块"""
        try:
            chunks = await self.document_repo.get_document_chunks(document_id)

            # 转换为响应Schema
            from modules.schemas.document import DocumentChunkResponse

            chunk_responses = []
            for chunk in chunks:
                chunk_responses.append(
                    DocumentChunkResponse(
                        id=chunk.id,
                        document_id=chunk.document_id,
                        content=chunk.content,
                        chunk_index=chunk.chunk_index,
                        start_char=chunk.start_char,
                        end_char=chunk.end_char,
                        embedding_vector=chunk.embedding_vector,
                        chunk_metadata=chunk.chunk_metadata or {},
                        created_at=chunk.created_at,
                        updated_at=chunk.updated_at,
                    )
                )

            return chunk_responses

        except Exception as e:
            self._handle_error(e, f"get_document_chunks_{document_id}")

    # 私有方法
    async def _validate_document_creation(self, document_data: DocumentCreate) -> None:
        """验证文档创建"""
        # 在Celery worker环境中跳过文件存在性验证以避免异步数据库操作
        # 因为Celery worker可能没有正确的异步上下文
        try:
            # 检查文件是否存在
            if document_data.file_id:
                file_record = await self.file_repo.get_file_by_id(document_data.file_id)
                if not file_record:
                    raise ValueError(f"文件 {document_data.file_id} 不存在")
        except Exception as e:
            # 在Celery worker或其他异步上下文问题时，记录警告但不阻止文档创建
            logger.warning(f"文件验证跳过: {e}")
            logger.info("在Celery worker环境中跳过文件存在性验证")

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
                end_char=end,
            )

            chunks.append(chunk_content)
            start = end - chunk_overlap
            chunk_index += 1

            if start >= len(content):
                break

        return len(chunks)

    # ========================
    # RAG Pipeline Integration
    # ========================

    async def initialize_rag_pipeline(
        self,
        embedding_provider: str = None,
        vector_store_provider: str = "weaviate",
        **config_kwargs,
    ) -> None:
        """Initialize RAG processing pipeline using configuration system"""
        if not self.enable_rag:
            logger.info("RAG feature disabled, skipping initialization")
            return

        try:
            # Get AI configuration
            from config import get_config

            config = get_config()
            ai_config = config.ai

            # Use provider from config if not specified
            if embedding_provider is None:
                embedding_provider = ai_config.embedding.provider

            # Import dynamically to avoid circular import
            from modules.models import ModuleConfig
            from modules.services.rag_service import (
                create_document_pipeline,
                create_embedding_service,
                create_vector_store,
            )

            document_metadata = config_kwargs.get("document_metadata", {})

            logger.info(f"got document metadata: {document_metadata}")

            content_type_str = document_metadata.get("detected_type", {})
            content_type = (
                ContentType(content_type_str) if content_type_str else ContentType.TXT
            )
            file_loader = FileLoaderFactory.get_loader(content_type)

            # Document processor
            document_processor = ChunkingProcessor(
                default_chunk_size=ai_config.embedding.chunk_size,
                default_overlap=ai_config.embedding.overlap,
                min_chunk_size=50,
                max_chunk_size=4000,
            )

            # Embedding service with AI configuration
            embedding_service = create_embedding_service(
                provider=EmbeddingProvider(embedding_provider),
                ai_config=ai_config,
                **config_kwargs.get("embedding", {}),
            )

            # Vector store
            vector_store = create_vector_store(
                provider=VectorStoreProvider(vector_store_provider),
                **config_kwargs.get("vector_store", {}),
            )

            # Create pipeline
            self._rag_pipeline = create_document_pipeline(
                file_loader=file_loader,
                document_processor=document_processor,
                embedding_service=embedding_service,
                vector_store=vector_store,
                **config_kwargs.get("pipeline", {}),
            )

            # Initialize pipeline
            await self._rag_pipeline.initialize()
            self._rag_initialized = True

            logger.info("RAG Pipeline initialized successfully")

        except Exception as e:
            logger.error(f"RAG Pipeline initialization failed: {e}")
            self._rag_initialized = False
            raise

    async def process_file_through_rag_pipeline(
        self,
        file_id: str,
        file_path: str,
        content_type: Optional[ContentType] = None,
        topic_id: Optional[int] = None,
        priority: int = 0,
    ) -> Optional[str]:
        """通过RAG管道处理文件"""
        if not self.enable_rag or not self._rag_initialized:
            logger.warning("RAG is not initialized or disabled, skipping processing")
            return None

        try:
            # Create processing request
            request = DocumentProcessingRequest(
                file_id=file_id,
                file_path=file_path,
                topic_id=topic_id,
                priority=priority,
                content_type=content_type,
                metadata={
                    "processed_by": "DocumentService",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            # Process through pipeline
            result = await self._rag_pipeline.process_document(request)

            # Log result
            if result.status == PipelineStatus.COMPLETED:
                logger.info(
                    f"RAG处理完成: {file_id}, 创建了 {result.total_chunks} 个块, "
                    f"生成了 {result.embedded_chunks} 个嵌入向量, "
                    f"存储了 {result.stored_vectors} 个向量"
                )
            else:
                logger.error(f"RAG处理失败: {file_id}, 错误: {result.error_message}")

            return result.request_id

        except Exception as e:
            logger.error(f"RAG管道处理失败: {e}")
            raise

    async def get_rag_processing_status(
        self, request_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取RAG处理状态"""
        if not self.enable_rag or not self._rag_initialized:
            return None

        try:
            progress = await self._rag_pipeline.get_processing_status(request_id)
            if progress:
                return {
                    "request_id": progress.request_id,
                    "current_stage": progress.current_stage.value,
                    "progress_percentage": progress.progress_percentage,
                    "status": progress.current_status.value,
                    "estimated_remaining_ms": progress.estimated_remaining_ms,
                    "message": progress.message,
                    "timestamp": progress.timestamp.isoformat(),
                }
            return None

        except Exception as e:
            logger.error(f"获取RAG处理状态失败: {e}")
            return None

    async def cancel_rag_processing(self, request_id: str) -> bool:
        """取消RAG处理"""
        if not self.enable_rag or not self._rag_initialized:
            return False

        try:
            return await self._rag_pipeline.cancel_processing(request_id)
        except Exception as e:
            logger.error(f"取消RAG处理失败: {e}")
            return False

    async def search_documents_with_rag(
        self,
        query: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        document_ids: Optional[List[str]] = None,
        topic_id: Optional[int] = None,
    ) -> SearchResponse:
        """使用RAG进行语义搜索"""
        if not self.enable_rag or not self._rag_initialized:
            # Fallback to traditional search
            logger.warning("RAG未初始化，回退到传统搜索")
            request = SearchRequest(query=query, limit=limit)
            return await self.search_documents(request)

        try:
            start_time = datetime.utcnow()

            # Generate query embedding
            embedding_service = self._rag_pipeline._embedding_service
            query_vector = await embedding_service.generate_single_embedding(query)

            # Search in vector store
            from modules.vector_store import SearchFilter

            filters = SearchFilter()
            if document_ids:
                filters.document_ids = document_ids
            if topic_id:
                filters.metadata_filters = {"topic_id": topic_id}

            vector_store = self._rag_pipeline._vector_store
            vector_results = await vector_store.search_similar(
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters,
            )

            # Convert to SearchResponse format
            from modules.schemas.responses import SearchResult

            results = []
            for vector_result in vector_results:
                results.append(
                    SearchResult(
                        document_id=vector_result.document.document_id or "",
                        title=vector_result.document.metadata.get("document_title", ""),
                        content=vector_result.document.content,
                        score=vector_result.score,
                        content_type="text",
                        file_id=vector_result.document.metadata.get("file_id", ""),
                        metadata=vector_result.document.metadata,
                    )
                )

            search_time = (datetime.utcnow() - start_time).total_seconds()

            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time=search_time,
                search_type="semantic_rag",
            )

        except Exception as e:
            logger.error(f"RAG搜索失败: {e}")
            # Fallback to traditional search
            request = SearchRequest(query=query, limit=limit)
            return await self.search_documents(request)

    async def get_rag_pipeline_health(self) -> Dict[str, Any]:
        """获取RAG管道健康状态"""
        if not self.enable_rag or not self._rag_initialized:
            return {"status": "disabled", "message": "RAG功能未启用或未初始化"}

        try:
            return await self._rag_pipeline.health_check()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def cleanup_rag_pipeline(self) -> None:
        """清理RAG管道资源"""
        if self._rag_pipeline:
            try:
                await self._rag_pipeline.cleanup()
                self._rag_initialized = False
                logger.info("RAG管道资源清理完成")
            except Exception as e:
                logger.error(f"RAG管道清理失败: {e}")

    # ========================
    # Enhanced Document Methods
    # ========================

    async def create_document_with_rag(
        self,
        document_data: DocumentCreate,
        trigger_rag_processing: bool = True,
        topic_id: Optional[int] = None,
    ) -> DocumentResponse:
        """创建文档并可选择触发RAG处理"""
        try:
            # Create document normally
            document_response = await self.create_document(document_data)

            # Trigger RAG processing if enabled
            if trigger_rag_processing and self.enable_rag and document_data.file_path:
                try:
                    request_id = await self.process_file_through_rag_pipeline(
                        file_id=document_data.file_id or document_response.id,
                        file_path=document_data.file_path,
                        content_type=document_data.content_type,
                        topic_id=topic_id,
                    )

                    if request_id:
                        # Add RAG processing info to metadata
                        document_response.doc_metadata = (
                            document_response.doc_metadata or {}
                        )
                        document_response.doc_metadata["rag_request_id"] = request_id
                        document_response.doc_metadata["rag_processing_triggered"] = (
                            True
                        )

                except Exception as e:
                    logger.error(f"RAG处理触发失败: {e}")
                    # Don't fail the document creation, just log the error

            return document_response

        except Exception as e:
            self._handle_error(e, "create_document_with_rag")


def create_document_service(
    session: AsyncSession, enable_rag: bool = True
) -> DocumentService:
    """创建Document service实例"""
    return DocumentService(session=session, enable_rag=enable_rag)
