"""
RAG Task Handlers

Contains various async task handlers for the RAG system:
- Document processing pipeline
- Embedding vector generation
- Vector storage operations
- Document search functionality
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from logging_system import (
    get_logger,
    log_errors,
    log_execution_time,
    task_context,
)
from modules import schemas
from modules.embedding import EmbeddingProvider
from modules.pipeline import (
    DocumentProcessingRequest,
    PipelineConfig,
    PipelineStatus,
)
from modules.vector_store import VectorStoreProvider
from modules.services.task_service import register_task_handler, task_handler
from modules.tasks.base import ITaskHandler, TaskPriority, TaskProgress

logger = get_logger(__name__)


@task_handler(
    schemas.TaskName.RAG_PROCESS_DOCUMENT.value,
    priority=TaskPriority.HIGH,
    max_retries=3,
    timeout=600,  # 10分钟超时
    queue="rag_queue",
)
@task_handler(
    schemas.TaskName.RAG_PROCESS_DOCUMENT_ASYNC.value, 
    priority=TaskPriority.HIGH,
    max_retries=3,
    timeout=600,  # 10分钟超时
    queue="rag_queue",
)
@register_task_handler
class DocumentProcessingHandler(ITaskHandler):
    """Document processing task handler - executes complete RAG document processing pipeline"""

    @property
    def task_name(self) -> str:
        return schemas.TaskName.RAG_PROCESS_DOCUMENT.value  # 主要任务名

    @log_execution_time(threshold_ms=1000)
    async def handle(
        self,
        file_id: str,
        file_path: str,
        topic_id: Optional[int] = None,
        document_id: Optional[str] = None,  # 支持传入document_id
        content_type: Optional[str] = None,  # 支持传入content_type
        embedding_provider: str = "openai",
        vector_store_provider: str = "weaviate",
        chunking_config: Optional[Dict[str, Any]] = None,  # 新的chunking配置
        **config,
    ) -> Dict[str, Any]:
        """
        处理文档的完整RAG管道

        Args:
            file_id: 文件ID
            file_path: 文件路径
            topic_id: 主题ID
            document_id: 文档ID（可选，用于异步处理）
            content_type: 内容类型（可选）
            embedding_provider: 嵌入服务提供商
            vector_store_provider: 向量存储提供商
            chunking_config: 分块配置（可选）
            **config: 其他配置参数

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            with task_context(
                task_id=f"rag-{file_id}",
                task_name="rag.process_document",
                queue="rag_queue",
            ):
                logger.info(f"开始RAG文档处理: {file_id} at {file_path}")

                # 初始化Chunking集成系统
                from ...rag.chunking.integration import initialize_chunking_integration
                await initialize_chunking_integration()

                # 更新文件状态为处理中
                await self._update_file_status(
                    file_id, "processing", "RAG处理中: 初始化组件"
                )

            # 动态导入以避免循环依赖
            from ...file_loader import MultiFormatFileLoader
            from ...models import ModuleConfig
            from ...rag.processors.enhanced_chunking_processor import EnhancedChunkingProcessor
            from ...services.rag_service import create_document_pipeline

            # 更新进度: 初始化
            await self._update_progress("初始化RAG管道组件", 0, 100)

            # 创建组件配置
            module_config = ModuleConfig("rag_task")
            pipeline_config = PipelineConfig(
                chunk_size=config.get("chunk_size", 1000),
                chunk_overlap=config.get("chunk_overlap", 200),
                enable_embeddings=config.get("enable_embeddings", True),
                enable_vector_storage=config.get("enable_vector_storage", True),
                batch_size=config.get("batch_size", 50),
                **config.get("pipeline_config", {}),
            )

            # 更新文件状态
            await self._update_file_status(
                file_id, "processing", "RAG处理中: 创建管道组件"
            )

            # 创建RAG管道组件
            from ...services.rag_service import (
                create_embedding_service,
                create_vector_store,
            )

            # 更新进度: 创建组件
            await self._update_progress("创建RAG管道组件", 10, 100)

            file_loader = MultiFormatFileLoader(module_config)
            
            # 使用增强的分块处理器
            processor_config = {
                "default_chunk_size": pipeline_config.chunk_size,
                "default_overlap": pipeline_config.chunk_overlap,
            }
            
            # 合并chunking_config参数
            if chunking_config:
                logger.info(f"应用智能分块配置: {chunking_config}")
                processor_config.update(chunking_config)
                
                # 如果有推荐策略，应用到处理器配置
                if "recommended_strategy" in chunking_config:
                    processor_config["preferred_strategy"] = chunking_config["recommended_strategy"]
            
            # 合并其他配置
            processor_config.update(config.get("chunking_config", {}))
            
            document_processor = EnhancedChunkingProcessor(**processor_config)

            embedding_service = create_embedding_service(
                provider=EmbeddingProvider(embedding_provider),
                **config.get("embedding_config", {}),
            )

            vector_store = create_vector_store(
                provider=VectorStoreProvider(vector_store_provider),
                **config.get("vector_store_config", {}),
            )

            # 创建文档处理管道
            pipeline = create_document_pipeline(
                file_loader=file_loader,
                document_processor=document_processor,
                embedding_service=embedding_service,
                vector_store=vector_store,
                **pipeline_config.__dict__,
            )

            # 更新进度: 初始化管道
            await self._update_progress("初始化处理管道", 20, 100)
            await self._update_file_status(
                file_id, "processing", "RAG处理中: 初始化处理管道"
            )

            # 初始化管道
            await pipeline.initialize()

            # 创建处理请求
            request = DocumentProcessingRequest(
                file_id=file_id,
                file_path=file_path,
                topic_id=topic_id,
                config=pipeline_config,
                metadata={
                    "task_type": "async_processing",
                    "embedding_provider": embedding_provider,
                    "vector_store_provider": vector_store_provider,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            # 更新进度: 开始处理
            await self._update_progress("开始文档处理", 30, 100)
            await self._update_file_status(
                file_id, "processing", "RAG处理中: 文档解析和分块"
            )

            # 执行处理
            result = await pipeline.process_document(request)

            # 检查处理结果
            if result.status == PipelineStatus.COMPLETED:
                # 更新进度: 处理完成
                await self._update_progress("处理完成", 100, 100)
                await self._update_file_status(
                    file_id,
                    "available",  # RAG处理完成后设置为available状态，用户可以开始查询
                    f"RAG处理完成: {result.total_chunks}块, {result.stored_vectors}向量",
                )
                logger.info(f"🎉 文件 {file_id} RAG处理完成，状态更新为available，用户可以开始查询")
            else:
                # 处理失败
                await self._update_file_status(
                    file_id, "failed", "RAG处理失败", error_message=result.error_message
                )
                logger.error(f"❌ 文件 {file_id} RAG处理失败，状态更新为failed")

            # 清理资源
            await pipeline.cleanup()

            # 构建返回结果
            processing_result = {
                "success": result.status == PipelineStatus.COMPLETED,
                "file_id": file_id,
                "document_id": result.document_id,
                "request_id": result.request_id,
                "status": result.status.value,
                "chunks_created": result.total_chunks,
                "embeddings_created": result.embedded_chunks,
                "vectors_stored": result.stored_vectors,
                "processing_time_ms": result.total_processing_time_ms,
                "stage_results": [
                    {
                        "stage": stage.stage.value,
                        "status": stage.status.value,
                        "time_ms": stage.processing_time_ms,
                        "items_processed": stage.items_processed,
                    }
                    for stage in result.stage_results
                ],
                "metadata": result.metadata,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

            if not processing_result["success"]:
                processing_result["error"] = result.error_message

            logger.info(
                f"RAG文档处理完成: {file_id}, 成功: {processing_result['success']}"
            )
            return processing_result

        except Exception as e:
            logger.error(f"RAG文档处理失败: {file_id}, {e}")

            # 更新文件状态为失败
            await self._update_file_status(
                file_id, "failed", "RAG处理失败", error_message=str(e)
            )
            logger.error(f"❌ 文件 {file_id} RAG处理异常失败，状态更新为failed")

            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.now(timezone.utc).isoformat(),
            }

    async def _update_progress(self, description: str, current: int, total: int):
        """更新任务进度"""
        # 这里需要获取当前任务的task_id，在实际Celery环境中可以获取
        # 暂时使用占位符实现
        try:
            progress = TaskProgress(
                task_id="current_task",  # 在实际使用中会被替换
                current=current,
                total=total,
                description=description,
            )
            logger.info(f"进度更新: {description} ({current}/{total})")
        except Exception as e:
            logger.debug(f"进度更新失败: {e}")

    async def _update_file_status(
        self,
        file_id: str,
        status: str,
        processing_status: str,
        error_message: Optional[str] = None,
    ):
        """更新文件处理状态
        
        Args:
            file_id: 文件ID
            status: 文件状态，应使用FileStatus枚举对应的字符串值
            processing_status: 处理状态描述
            error_message: 错误信息（可选）
        """
        try:
            from ...database import get_db_session
            from ...repository import FileRepository

            session_gen = get_db_session()
            session = await session_gen.__anext__()
            try:
                file_repo = FileRepository(session)
                await file_repo.update_file_status(
                    file_id=file_id,
                    status=status,  # 接收字符串，由repository层处理枚举映射
                    processing_status=processing_status,
                    error_message=error_message,
                )
                logger.info(f"📋 文件状态更新: {file_id} -> {status}: {processing_status}")
            finally:
                await session.close()
        except Exception as e:
            logger.warning(f"⚠️ 文件状态更新失败: {file_id}, {e}")
            # 不让状态更新失败影响主流程


@task_handler(
    schemas.TaskName.RAG_GENERATE_EMBEDDINGS.value,
    priority=TaskPriority.NORMAL,
    max_retries=2,
    timeout=300,
    queue="rag_queue",
)
@register_task_handler
class EmbeddingGenerationHandler(ITaskHandler):
    """嵌入向量生成任务处理器"""

    @property
    def task_name(self) -> str:
        return schemas.TaskName.RAG_GENERATE_EMBEDDINGS.value

    @log_execution_time(threshold_ms=500)
    @log_errors()
    async def handle(
        self,
        texts: List[str],
        provider: str = "openai",
        model_name: Optional[str] = None,
        **config,
    ) -> Dict[str, Any]:
        """
        生成文本嵌入向量

        Args:
            texts: 待嵌入的文本列表
            provider: 嵌入服务提供商
            model_name: 模型名称
            **config: 其他配置

        Returns:
            Dict[str, Any]: 嵌入结果
        """
        try:
            with task_context(
                task_id=f"embedding-{len(texts)}-texts",
                task_name="rag.generate_embeddings",
                queue="rag_queue",
            ):
                logger.info(f"开始生成嵌入向量: {len(texts)} 个文本")

            from ...rag.embedding import EmbeddingProvider
            from ...services.rag_service import create_embedding_service

            # 创建嵌入服务
            embedding_config = config.copy()
            if model_name:
                embedding_config["model_name"] = model_name

            embedding_service = create_embedding_service(
                provider=EmbeddingProvider(provider), **embedding_config
            )

            # 初始化服务
            await embedding_service.initialize()

            # 生成嵌入
            result = await embedding_service.generate_embeddings(texts)

            # 清理服务
            await embedding_service.cleanup()

            return {
                "success": True,
                "vectors": result.vectors,
                "texts": result.texts,
                "model_name": result.model_name,
                "dimension": result.dimension,
                "processing_time_ms": result.processing_time_ms,
                "metadata": result.metadata,
                "provider": provider,
            }

        except Exception as e:
            logger.error(f"嵌入向量生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "provider": provider,
                "text_count": len(texts),
            }


@task_handler(
    schemas.TaskName.RAG_STORE_VECTORS.value,
    priority=TaskPriority.NORMAL,
    max_retries=3,
    timeout=180,
    queue="rag_queue",
)
@register_task_handler
class VectorStorageHandler(ITaskHandler):
    """向量存储任务处理器"""

    @property
    def task_name(self) -> str:
        return schemas.TaskName.RAG_STORE_VECTORS.value

    @log_execution_time(threshold_ms=800)
    @log_errors()
    async def handle(
        self,
        vectors: List[List[float]],
        contents: List[str],
        document_id: str,
        provider: str = "weaviate",
        collection_name: str = "documents",
        **config,
    ) -> Dict[str, Any]:
        """
        存储向量到向量数据库

        Args:
            vectors: 向量列表
            contents: 对应的内容列表
            document_id: 文档ID
            provider: 向量存储提供商
            collection_name: 集合名称
            **config: 其他配置

        Returns:
            Dict[str, Any]: 存储结果
        """
        try:
            with task_context(
                task_id=f"store-{document_id}-vectors",
                task_name="rag.store_vectors",
                queue="rag_queue",
            ):
                logger.info(f"开始存储向量: {len(vectors)} 个向量")

            from ...rag.vector_store import VectorDocument, VectorStoreProvider
            from ...services.rag_service import create_vector_store

            # 创建向量存储服务
            vector_store_config = config.copy()
            vector_store_config["collection_name"] = collection_name

            vector_store = create_vector_store(
                provider=VectorStoreProvider(provider), **vector_store_config
            )

            # 初始化服务
            await vector_store.initialize()

            # 创建向量文档
            vector_docs = []
            for i, (vector, content) in enumerate(zip(vectors, contents)):
                vector_doc = VectorDocument(
                    id=f"{document_id}_chunk_{i}",
                    vector=vector,
                    content=content,
                    metadata={
                        "document_id": document_id,
                        "chunk_index": i,
                        "stored_at": datetime.now(timezone.utc).isoformat(),
                    },
                    document_id=document_id,
                    chunk_index=i,
                )
                vector_docs.append(vector_doc)

            # 批量存储向量
            result = await vector_store.upsert_vectors(vector_docs)

            # 清理服务
            await vector_store.cleanup()

            return {
                "success": True,
                "document_id": document_id,
                "vectors_stored": result.success_count,
                "vectors_failed": result.failed_count,
                "total_vectors": result.total_count,
                "processing_time_ms": result.processing_time_ms,
                "errors": result.errors,
                "provider": provider,
                "collection_name": collection_name,
            }

        except Exception as e:
            logger.error(f"向量存储失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "document_id": document_id,
                "vector_count": len(vectors),
            }


@task_handler(
    schemas.TaskName.RAG_SEMANTIC_SEARCH.value,
    priority=TaskPriority.HIGH,
    max_retries=2,
    timeout=60,
    queue="search_queue",
)
@register_task_handler
class SemanticSearchHandler(ITaskHandler):
    """语义搜索任务处理器"""

    @property
    def task_name(self) -> str:
        return schemas.TaskName.RAG_SEMANTIC_SEARCH.value

    @log_execution_time(threshold_ms=300)
    @log_errors()
    async def handle(
        self,
        query: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        embedding_provider: str = "openai",
        vector_store_provider: str = "weaviate",
        **config,
    ) -> Dict[str, Any]:
        """
        执行语义搜索

        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            score_threshold: 相似性分数阈值
            embedding_provider: 嵌入服务提供商
            vector_store_provider: 向量存储提供商
            **config: 其他配置

        Returns:
            Dict[str, Any]: 搜索结果
        """
        try:
            with task_context(
                task_id=f"search-{hash(query) % 10000}",
                task_name="rag.semantic_search",
                queue="search_queue",
            ):
                logger.info(f"开始语义搜索: {query}")

            from ...rag.embedding import EmbeddingProvider
            from ...rag.vector_store import SearchFilter, VectorStoreProvider
            from ...services.rag_service import (
                create_embedding_service,
                create_vector_store,
            )

            # 创建嵌入服务
            embedding_service = create_embedding_service(
                provider=EmbeddingProvider(embedding_provider),
                **config.get("embedding_config", {}),
            )

            # 创建向量存储服务
            vector_store = create_vector_store(
                provider=VectorStoreProvider(vector_store_provider),
                **config.get("vector_store_config", {}),
            )

            # 初始化服务
            await embedding_service.initialize()
            await vector_store.initialize()

            # 生成查询向量
            query_vector = await embedding_service.generate_single_embedding(query)

            # 创建搜索过滤器
            filters = SearchFilter()
            if "document_ids" in config:
                filters.document_ids = config["document_ids"]
            if "metadata_filters" in config:
                filters.metadata_filters = config["metadata_filters"]

            # 执行相似性搜索
            search_results = await vector_store.search_similar(
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters,
            )

            # 清理服务
            await embedding_service.cleanup()
            await vector_store.cleanup()

            # 格式化结果
            results = []
            for search_result in search_results:
                results.append(
                    {
                        "document_id": search_result.document.document_id,
                        "content": search_result.document.content,
                        "score": search_result.score,
                        "rank": search_result.rank,
                        "metadata": search_result.document.metadata,
                    }
                )

            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results),
                "embedding_provider": embedding_provider,
                "vector_store_provider": vector_store_provider,
                "search_time": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__,
            }


@task_handler(
    schemas.TaskName.RAG_CLEANUP_DOCUMENT.value,
    priority=TaskPriority.LOW,
    max_retries=2,
    timeout=120,
    queue="cleanup_queue",
)
@register_task_handler
class DocumentCleanupHandler(ITaskHandler):
    """文档清理任务处理器"""

    @property
    def task_name(self) -> str:
        return schemas.TaskName.RAG_CLEANUP_DOCUMENT.value

    @log_execution_time(threshold_ms=400)
    @log_errors()
    async def handle(
        self, document_id: str, vector_store_provider: str = "weaviate", **config
    ) -> Dict[str, Any]:
        """
        清理文档相关的向量和数据

        Args:
            document_id: 文档ID
            vector_store_provider: 向量存储提供商
            **config: 其他配置

        Returns:
            Dict[str, Any]: 清理结果
        """
        try:
            with task_context(
                task_id=f"cleanup-{document_id}",
                task_name="rag.cleanup_document",
                queue="cleanup_queue",
            ):
                logger.info(f"开始清理文档: {document_id}")

            from ...rag.vector_store import VectorStoreProvider
            from ...services.rag_service import create_vector_store

            # 创建向量存储服务
            vector_store = create_vector_store(
                provider=VectorStoreProvider(vector_store_provider),
                **config.get("vector_store_config", {}),
            )

            # 初始化服务
            await vector_store.initialize()

            # 删除文档相关向量
            result = await vector_store.delete_vectors_by_document_id(document_id)

            # 清理服务
            await vector_store.cleanup()

            return {
                "success": True,
                "document_id": document_id,
                "vectors_deleted": result.success_count,
                "cleanup_time": datetime.now(timezone.utc).isoformat(),
                "provider": vector_store_provider,
            }

        except Exception as e:
            logger.error(f"文档清理失败: {e}")
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e),
                "error_type": type(e).__name__,
            }


@task_handler(
    schemas.TaskName.RAG_PROCESS_DOCUMENT_ASYNC.value,
    priority=TaskPriority.HIGH,
    max_retries=3,
    timeout=600,
    queue="rag_queue",
)
@register_task_handler
class AsyncDocumentProcessingHandler(ITaskHandler):
    """异步文档RAG处理任务处理器 - 在独立的异步上下文中处理RAG"""

    @property
    def task_name(self) -> str:
        return schemas.TaskName.RAG_PROCESS_DOCUMENT_ASYNC.value

    @log_execution_time(threshold_ms=1000)
    async def handle(
        self,
        file_id: str = None,
        document_id: str = None,
        file_path: str = None,
        content_type: str = "txt",
        topic_id: Optional[int] = None,
        embedding_provider: str = "openai",
        vector_store_provider: str = "weaviate",
        execution_id: str = None,
        workflow_id: str = None,
        orchestrated: bool = False,
        chunking_config: Optional[Dict[str, Any]] = None,
        **config,
    ) -> Dict[str, Any]:
        """
        在独立的异步上下文中处理文档RAG

        Args:
            file_id: 文件ID
            document_id: 文档ID
            file_path: 文件路径
            content_type: 内容类型
            topic_id: 主题ID
            embedding_provider: 嵌入服务提供商
            vector_store_provider: 向量存储提供商
            execution_id: 工作流执行ID (当被工作流调用时)
            workflow_id: 工作流ID (当被工作流调用时)
            orchestrated: 是否由工作流编排调用
            **config: 其他配置参数

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 处理工作流编排的情况
            if orchestrated and execution_id:
                context_info = f"workflow-{execution_id}"
                logger.info(f"RAG任务由工作流编排调用: {execution_id}")
            else:
                context_info = f"standalone-{document_id or file_id}"
                logger.info(f"RAG任务独立调用: {document_id or file_id}")

            with task_context(
                task_id=f"rag-async-{context_info}",
                task_name="rag.process_document_async",
                queue="rag_queue",
            ):
                logger.info(f"开始异步RAG文档处理: {document_id} (file: {file_id})")

                # 验证必要参数
                if not document_id:
                    raise ValueError("document_id 是必需的参数")
                if not file_path:
                    raise ValueError("file_path 是必需的参数")

                # 获取存储服务并下载文件
                from ...storage.base import create_storage_service

                storage = create_storage_service()

                # 获取文件信息（包括原始文件名）
                file_info = await self._get_file_info(file_id) if file_id else {}
                original_filename = file_info.get("original_name")

                # 下载文件到临时位置
                temp_file_path = await self._download_file_to_temp(
                    storage, file_path, file_id or document_id
                )

                try:
                    # 使用工厂模式加载文档，传递原始文件名
                    from modules.schemas.enums import ContentType

                    from ...file_loader import detect_content_type, load_document

                    # 转换内容类型
                    try:
                        ct = ContentType(content_type)
                    except ValueError:
                        ct = detect_content_type(temp_file_path)

                    # 加载文档，传递原始文件名到metadata中
                    document = await load_document(
                        temp_file_path, 
                        ct, 
                        original_filename=original_filename
                    )
                    logger.info(
                        f"Document loaded: {document.title}, content length: {len(document.content)}"
                    )

                    # 初始化RAG管道
                    await self._initialize_rag_pipeline(
                        embedding_provider, vector_store_provider
                    )

                    # 设置分块配置
                    if chunking_config:
                        self._current_chunking_config = chunking_config
                        logger.info(f"使用自定义分块配置: {chunking_config}")

                    # 处理文档
                    result = await self._process_with_rag_pipeline(
                        document, document_id, file_id, topic_id
                    )

                    # 更新文档元数据
                    await self._update_document_metadata(document_id, result)

                    logger.info(f"异步RAG处理完成: {document_id}")

                    return {
                        "success": True,
                        "document_id": document_id,
                        "file_id": file_id or document_id,
                        "chunks_created": result.get("chunks_created", 0),
                        "embeddings_generated": result.get("embeddings_generated", 0),
                        "vectors_stored": result.get("vectors_stored", 0),
                        "processing_time_ms": result.get("processing_time_ms", 0),
                        "processed_at": datetime.now(timezone.utc).isoformat(),
                        # 工作流相关信息
                        "orchestrated": orchestrated,
                        "execution_id": execution_id,
                        "workflow_id": workflow_id,
                        "task_type": "rag.process_document_async",
                        "embedding_provider": embedding_provider,
                        "vector_store_provider": vector_store_provider,
                    }

                finally:
                    # 清理临时文件
                    import os

                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        logger.debug(f"临时文件已删除: {temp_file_path}")

        except Exception as e:
            logger.error(f"异步RAG文档处理失败: {document_id}, {e}")

            # 更新文档状态为处理失败
            try:
                await self._update_document_metadata(
                    document_id,
                    {
                        "rag_processing_status": "failed",
                        "rag_error": str(e),
                        "rag_failed_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            except Exception as update_error:
                logger.error(f"更新文档元数据失败: {update_error}")

            return {
                "success": False,
                "document_id": document_id,
                "file_id": file_id or document_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.now(timezone.utc).isoformat(),
                # 工作流相关信息
                "orchestrated": orchestrated,
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "task_type": "rag.process_document_async",
            }

    async def _download_file_to_temp(
        self, storage, file_path: str, file_id: str
    ) -> str:
        """从存储中下载文件到临时目录"""
        import os
        import tempfile

        import aiofiles

        # 创建临时文件
        suffix = os.path.splitext(file_path)[1] or ".tmp"
        temp_fd, temp_file_path = tempfile.mkstemp(
            suffix=suffix, prefix=f"rag_async_{file_id}_"
        )
        os.close(temp_fd)

        try:
            # 从存储中读取文件内容
            file_content = await storage.read_file(file_path)

            # 写入临时文件
            async with aiofiles.open(temp_file_path, "wb") as f:
                await f.write(file_content)

            logger.debug(f"文件已下载到临时位置: {temp_file_path}")
            return temp_file_path

        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise Exception(f"下载文件到临时目录失败: {e}")

    async def _initialize_rag_pipeline(
        self, embedding_provider: str, vector_store_provider: str
    ):
        """初始化RAG管道"""
        try:
            # 这里简化处理，实际可以根据需要初始化完整的RAG管道
            logger.info(
                f"RAG管道配置: embedding={embedding_provider}, vector_store={vector_store_provider}"
            )

            # TODO: 根据实际需要初始化嵌入服务和向量存储
            # 目前由于Celery worker环境的限制，这里只做配置检查

        except Exception as e:
            logger.warning(f"RAG管道初始化警告: {e}")

    async def _process_with_rag_pipeline(
        self, document, document_id: str, file_id: str, topic_id: Optional[int]
    ) -> Dict[str, Any]:
        """使用RAG管道处理文档"""
        try:
            # 获取RAG处理器实例
            rag_processor = await self._get_rag_processor()
            
            # 准备分块配置（如果有的话）
            chunking_config = getattr(self, '_chunking_config', {})
            
            # 如果从外部传入了分块配置，则使用它
            if hasattr(self, '_current_chunking_config') and self._current_chunking_config:
                chunking_config = self._current_chunking_config
            
            logger.info(f"开始RAG管道处理文档: {document_id}")
            
            # 调用真实的RAG处理器
            result = await rag_processor.process_document(
                document=document,
                chunking_config=chunking_config,
                topic_id=str(topic_id) if topic_id else None,
                file_id=file_id
            )
            
            # 转换结果格式
            return {
                "chunks_created": result.chunks_created,
                "embeddings_generated": result.embeddings_generated,
                "vectors_stored": result.vectors_stored,
                "processing_time_ms": result.processing_time_ms,
                "status": "completed" if result.status.value == "completed" else "failed",
                "strategy_used": result.strategy_used,
                "quality_score": result.quality_score,
                "error": result.error_message,
                "stage_details": result.stage_details,
            }

        except Exception as e:
            logger.error(f"RAG管道处理失败: {e}")
            return {
                "chunks_created": 0,
                "embeddings_generated": 0,
                "vectors_stored": 0,
                "processing_time_ms": 0,
                "status": "failed",
                "error": str(e),
            }
    
    async def _get_rag_processor(self):
        """获取RAG处理器实例"""
        from modules.services.rag_processor import RAGProcessor, RAGProcessorConfig
        from modules.embedding.openai_service import OpenAIEmbeddingService
        from modules.vector_store.weaviate_service import WeaviateVectorStore
        from config import get_config
        
        config = get_config()
        
        # 创建嵌入服务
        openai_config = config.ai.embedding.openai
        embedding_service = OpenAIEmbeddingService(
            api_key=getattr(config, 'openai_api_key', None) or openai_config.api_key,
            model="text-embedding-3-small",
            max_batch_size=50,
            http_proxy=openai_config.http_proxy,
            https_proxy=openai_config.https_proxy,
            api_base=openai_config.api_base,
        )
        
        # 创建向量存储服务
        vector_store = WeaviateVectorStore(
            url=getattr(config, 'weaviate_url', None) or config.vector_db.weaviate_url or "http://localhost:8080",
            api_key=getattr(config, 'weaviate_api_key', None),
            batch_size=50,
        )
        
        # 创建RAG处理器配置
        rag_config = RAGProcessorConfig(
            embedding_provider="openai",
            vector_store_provider="weaviate",
            collection_name="documents",
            batch_size=50,
            max_concurrent_embeddings=3,
        )
        
        # 创建RAG处理器
        rag_processor = RAGProcessor(
            config=rag_config,
            embedding_service=embedding_service,
            vector_store=vector_store,
        )
        
        return rag_processor

    async def _update_document_metadata(
        self, document_id: str, metadata: Dict[str, Any]
    ):
        """更新文档元数据"""
        try:
            from config import get_config

            from ...database.connection import DatabaseConnection
            from ...repository import DocumentRepository

            # 创建新的数据库连接
            config = get_config()
            db = DatabaseConnection(config.database.url)
            await db.initialize()

            async with db.get_session() as session:
                doc_repo = DocumentRepository(session)

                # 获取现有文档
                document = await doc_repo.get_document_by_id(document_id)
                if document:
                    # 更新元数据
                    current_metadata = document.doc_metadata or {}
                    current_metadata.update(
                        {
                            "rag_processing_status": metadata.get(
                                "status", "completed"
                            ),
                            "rag_chunks_created": metadata.get("chunks_created", 0),
                            "rag_embeddings_generated": metadata.get(
                                "embeddings_generated", 0
                            ),
                            "rag_vectors_stored": metadata.get("vectors_stored", 0),
                            "rag_processing_time_ms": metadata.get(
                                "processing_time_ms", 0
                            ),
                            "rag_processed_at": datetime.now(timezone.utc).isoformat(),
                            **metadata,
                        }
                    )

                    # 更新文档
                    await doc_repo.update_document_metadata(
                        document_id, current_metadata
                    )
                    await session.commit()

                    logger.info(f"文档元数据已更新: {document_id}")
                else:
                    logger.warning(f"文档未找到: {document_id}")

            await db.close()

        except Exception as e:
            logger.error(f"更新文档元数据失败: {e}")

    async def _get_file_info(self, file_id: str) -> Dict[str, Any]:
        """从数据库获取文件信息"""
        try:
            from ...database import get_db_session
            from ...repository import FileRepository
            
            session_gen = get_db_session()
            session = await session_gen.__anext__()
            try:
                file_repo = FileRepository(session)
                file_record = await file_repo.get_file_by_id(file_id)
                
                if file_record:
                    return {
                        "original_name": file_record.original_name,
                        "filename": file_record.filename,
                        "content_type": file_record.content_type,
                        "file_size": file_record.file_size,
                    }
                else:
                    logger.warning(f"文件记录未找到: {file_id}")
                    return {}
            finally:
                await session.close()
                    
        except Exception as e:
            logger.error(f"获取文件信息失败: {file_id}, {e}")
            return {}


logger.info("RAG任务处理器模块已加载")
