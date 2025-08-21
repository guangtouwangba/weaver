"""
RAG相关任务处理器

包含RAG系统的各种异步任务处理器：
- 文档处理管道
- 嵌入向量生成
- 向量存储
- 文档搜索
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..base import ITaskHandler, TaskConfig, TaskPriority, TaskProgress
from ...services.task_service import task_handler, register_task_handler
from ...rag.pipeline import DocumentProcessingRequest, PipelineConfig, PipelineStatus
from ...rag.embedding import EmbeddingProvider
from ...rag.vector_store import VectorStoreProvider, VectorDocument

logger = logging.getLogger(__name__)


@task_handler("rag.process_document", 
              priority=TaskPriority.HIGH, 
              max_retries=3,
              timeout=600,  # 10分钟超时
              queue="rag_queue")
@register_task_handler
class DocumentProcessingHandler(ITaskHandler):
    """文档处理任务处理器 - 执行完整的RAG文档处理管道"""
    
    @property
    def task_name(self) -> str:
        return "rag.process_document"
    
    async def handle(self, 
                    file_id: str, 
                    file_path: str, 
                    topic_id: Optional[int] = None,
                    embedding_provider: str = "openai",
                    vector_store_provider: str = "weaviate",
                    **config) -> Dict[str, Any]:
        """
        处理文档的完整RAG管道
        
        Args:
            file_id: 文件ID
            file_path: 文件路径
            topic_id: 主题ID
            embedding_provider: 嵌入服务提供商
            vector_store_provider: 向量存储提供商
            **config: 其他配置参数
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            logger.info(f"开始RAG文档处理: {file_id} at {file_path}")
            
            # 动态导入以避免循环依赖
            from ...services.rag_service import create_document_pipeline
            from ...file_loader import MultiFormatFileLoader
            from ...rag.processors import ChunkingProcessor
            from ...models import ModuleConfig
            
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
                **config.get("pipeline_config", {})
            )
            
            # 创建RAG管道组件
            from ...services.rag_service import (
                create_embedding_service, create_vector_store
            )
            
            # 更新进度: 创建组件
            await self._update_progress("创建RAG管道组件", 10, 100)
            
            file_loader = MultiFormatFileLoader(module_config)
            document_processor = ChunkingProcessor(module_config)
            
            embedding_service = create_embedding_service(
                provider=EmbeddingProvider(embedding_provider),
                **config.get("embedding_config", {})
            )
            
            vector_store = create_vector_store(
                provider=VectorStoreProvider(vector_store_provider),
                **config.get("vector_store_config", {})
            )
            
            # 创建文档处理管道
            pipeline = create_document_pipeline(
                file_loader=file_loader,
                document_processor=document_processor,
                embedding_service=embedding_service,
                vector_store=vector_store,
                **pipeline_config.__dict__
            )
            
            # 更新进度: 初始化管道
            await self._update_progress("初始化处理管道", 20, 100)
            
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
                    "started_at": datetime.utcnow().isoformat()
                }
            )
            
            # 更新进度: 开始处理
            await self._update_progress("开始文档处理", 30, 100)
            
            # 执行处理
            result = await pipeline.process_document(request)
            
            # 更新进度: 处理完成
            await self._update_progress("处理完成", 100, 100)
            
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
                        "items_processed": stage.items_processed
                    } for stage in result.stage_results
                ],
                "metadata": result.metadata,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            if not processing_result["success"]:
                processing_result["error"] = result.error_message
            
            logger.info(f"RAG文档处理完成: {file_id}, 成功: {processing_result['success']}")
            return processing_result
            
        except Exception as e:
            logger.error(f"RAG文档处理失败: {file_id}, {e}")
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat()
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
                description=description
            )
            logger.info(f"进度更新: {description} ({current}/{total})")
        except Exception as e:
            logger.debug(f"进度更新失败: {e}")


@task_handler("rag.generate_embeddings",
              priority=TaskPriority.NORMAL,
              max_retries=2,
              timeout=300,
              queue="rag_queue")
@register_task_handler  
class EmbeddingGenerationHandler(ITaskHandler):
    """嵌入向量生成任务处理器"""
    
    @property
    def task_name(self) -> str:
        return "rag.generate_embeddings"
    
    async def handle(self, 
                    texts: List[str], 
                    provider: str = "openai",
                    model_name: Optional[str] = None,
                    **config) -> Dict[str, Any]:
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
            logger.info(f"开始生成嵌入向量: {len(texts)} 个文本")
            
            from ...services.rag_service import create_embedding_service
            from ...rag.embedding import EmbeddingProvider
            
            # 创建嵌入服务
            embedding_config = config.copy()
            if model_name:
                embedding_config["model_name"] = model_name
            
            embedding_service = create_embedding_service(
                provider=EmbeddingProvider(provider),
                **embedding_config
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
                "provider": provider
            }
            
        except Exception as e:
            logger.error(f"嵌入向量生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "provider": provider,
                "text_count": len(texts)
            }


@task_handler("rag.store_vectors",
              priority=TaskPriority.NORMAL,
              max_retries=3,
              timeout=180,
              queue="rag_queue")
@register_task_handler
class VectorStorageHandler(ITaskHandler):
    """向量存储任务处理器"""
    
    @property
    def task_name(self) -> str:
        return "rag.store_vectors"
    
    async def handle(self,
                    vectors: List[List[float]],
                    contents: List[str],
                    document_id: str,
                    provider: str = "weaviate",
                    collection_name: str = "documents",
                    **config) -> Dict[str, Any]:
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
            logger.info(f"开始存储向量: {len(vectors)} 个向量")
            
            from ...services.rag_service import create_vector_store
            from ...rag.vector_store import VectorStoreProvider, VectorDocument
            
            # 创建向量存储服务
            vector_store_config = config.copy()
            vector_store_config["collection_name"] = collection_name
            
            vector_store = create_vector_store(
                provider=VectorStoreProvider(provider),
                **vector_store_config
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
                        "stored_at": datetime.utcnow().isoformat()
                    },
                    document_id=document_id,
                    chunk_index=i
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
                "collection_name": collection_name
            }
            
        except Exception as e:
            logger.error(f"向量存储失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "document_id": document_id,
                "vector_count": len(vectors)
            }


@task_handler("rag.semantic_search",
              priority=TaskPriority.HIGH,
              max_retries=2,
              timeout=60,
              queue="search_queue")
@register_task_handler
class SemanticSearchHandler(ITaskHandler):
    """语义搜索任务处理器"""
    
    @property
    def task_name(self) -> str:
        return "rag.semantic_search"
    
    async def handle(self,
                    query: str,
                    limit: int = 10,
                    score_threshold: Optional[float] = None,
                    embedding_provider: str = "openai",
                    vector_store_provider: str = "weaviate",
                    **config) -> Dict[str, Any]:
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
            logger.info(f"开始语义搜索: {query}")
            
            from ...services.rag_service import create_embedding_service, create_vector_store
            from ...rag.embedding import EmbeddingProvider
            from ...rag.vector_store import VectorStoreProvider, SearchFilter
            
            # 创建嵌入服务
            embedding_service = create_embedding_service(
                provider=EmbeddingProvider(embedding_provider),
                **config.get("embedding_config", {})
            )
            
            # 创建向量存储服务
            vector_store = create_vector_store(
                provider=VectorStoreProvider(vector_store_provider),
                **config.get("vector_store_config", {})
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
                filters=filters
            )
            
            # 清理服务
            await embedding_service.cleanup()
            await vector_store.cleanup()
            
            # 格式化结果
            results = []
            for search_result in search_results:
                results.append({
                    "document_id": search_result.document.document_id,
                    "content": search_result.document.content,
                    "score": search_result.score,
                    "rank": search_result.rank,
                    "metadata": search_result.document.metadata
                })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results),
                "embedding_provider": embedding_provider,
                "vector_store_provider": vector_store_provider,
                "search_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "error_type": type(e).__name__
            }


@task_handler("rag.cleanup_document",
              priority=TaskPriority.LOW,
              max_retries=2,
              timeout=120,
              queue="cleanup_queue")
@register_task_handler
class DocumentCleanupHandler(ITaskHandler):
    """文档清理任务处理器"""
    
    @property  
    def task_name(self) -> str:
        return "rag.cleanup_document"
    
    async def handle(self,
                    document_id: str,
                    vector_store_provider: str = "weaviate",
                    **config) -> Dict[str, Any]:
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
            logger.info(f"开始清理文档: {document_id}")
            
            from ...services.rag_service import create_vector_store
            from ...rag.vector_store import VectorStoreProvider
            
            # 创建向量存储服务
            vector_store = create_vector_store(
                provider=VectorStoreProvider(vector_store_provider),
                **config.get("vector_store_config", {})
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
                "cleanup_time": datetime.utcnow().isoformat(),
                "provider": vector_store_provider
            }
            
        except Exception as e:
            logger.error(f"文档清理失败: {e}")
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e),
                "error_type": type(e).__name__
            }


logger.info("RAG任务处理器模块已加载")