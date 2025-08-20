"""
文档编排器实现

协调文件加载、文档处理、存储和搜索等模块的交互。
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from .interface import IOrchestrator, OrchestrationError
from ..file_loader.interface import IFileLoader
from ..document_processor.interface import IDocumentProcessor
from ..models import (
    Document, DocumentChunk, ProcessingRequest, ProcessingResult,
    SearchRequest, SearchResult, OrchestrationRequest, OrchestrationResult,
    ProcessingStatus, ContentType, ChunkingStrategy
)

logger = logging.getLogger(__name__)


class DocumentOrchestrator(IOrchestrator):
    """文档编排器实现"""
    
    def __init__(self, 
                 file_loader: IFileLoader,
                 document_processor: IDocumentProcessor,
                 storage_backend: Optional[Any] = None,
                 search_backend: Optional[Any] = None,
                 enable_caching: bool = True,
                 max_concurrent_operations: int = 5):
        """
        初始化文档编排器
        
        Args:
            file_loader: 文件加载器
            document_processor: 文档处理器
            storage_backend: 存储后端（可选）
            search_backend: 搜索后端（可选）
            enable_caching: 是否启用缓存
            max_concurrent_operations: 最大并发操作数
        """
        self.file_loader = file_loader
        self.document_processor = document_processor
        self.storage_backend = storage_backend
        self.search_backend = search_backend
        self.enable_caching = enable_caching
        self.max_concurrent_operations = max_concurrent_operations
        
        # 内部状态
        self._document_cache: Dict[str, Document] = {}
        self._chunk_cache: Dict[str, List[DocumentChunk]] = {}
        self._processing_semaphore = asyncio.Semaphore(max_concurrent_operations)
        
        logger.info(f"初始化 {self.orchestrator_name}")
    
    @property
    def orchestrator_name(self) -> str:
        """获取编排器名称"""
        return "DocumentOrchestrator"
    
    @property
    def supported_operations(self) -> List[str]:
        """获取支持的操作列表"""
        return [
            "process_document_end_to_end",
            "search_documents", 
            "get_document_by_id",
            "get_chunks_by_document_id",
            "delete_document",
            "update_document_metadata",
            "health_check"
        ]
    
    async def process_document_end_to_end(self, request: OrchestrationRequest) -> OrchestrationResult:
        """端到端处理文档"""
        start_time = asyncio.get_event_loop().time()
        operation_id = f"orch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{request.source_path.split('/')[-1]}"
        
        try:
            async with self._processing_semaphore:
                logger.info(f"开始端到端处理: {operation_id}")
                
                # 步骤1: 加载文件
                logger.debug(f"步骤1: 加载文件 {request.source_path}")
                document = await self._load_file(request)
                
                # 步骤2: 处理文档
                logger.debug(f"步骤2: 处理文档 {document.id}")
                processing_request = ProcessingRequest(
                    document=document,
                    chunking_strategy=request.chunking_strategy,
                    chunk_size=request.chunk_size,
                    chunk_overlap=request.chunk_overlap,
                    generate_embeddings=request.generate_embeddings
                )
                processing_result = await self._process_document(processing_request)
                
                # 步骤3: 存储文档和块
                if self.storage_backend:
                    logger.debug(f"步骤3: 存储文档数据")
                    await self._store_document_data(document, processing_result.chunks)
                
                # 步骤4: 构建搜索索引
                if self.search_backend and processing_result.chunks:
                    logger.debug(f"步骤4: 构建搜索索引")
                    await self._build_search_index(processing_result.chunks)
                
                # 步骤5: 缓存结果
                if self.enable_caching:
                    self._document_cache[document.id] = document
                    self._chunk_cache[document.id] = processing_result.chunks
                
                # 计算总处理时间
                total_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # 创建编排结果
                result = OrchestrationResult(
                    operation_id=operation_id,
                    document_id=document.id,
                    status=ProcessingStatus.COMPLETED,
                    chunks_created=len(processing_result.chunks),
                    total_processing_time_ms=total_time,
                    steps_completed=[
                        {"step": "file_loading", "status": "completed", "time_ms": 0},
                        {"step": "document_processing", "status": "completed", "time_ms": processing_result.processing_time_ms},
                        {"step": "storage", "status": "completed" if self.storage_backend else "skipped", "time_ms": 0},
                        {"step": "indexing", "status": "completed" if self.search_backend else "skipped", "time_ms": 0}
                    ],
                    metadata={
                        "orchestrator": self.orchestrator_name,
                        "file_loader": self.file_loader.loader_name,
                        "document_processor": self.document_processor.processor_name,
                        "document_metadata": document.metadata,
                        "processing_metadata": processing_result.metadata
                    }
                )
                
                logger.info(f"端到端处理完成: {operation_id}, 耗时 {total_time:.2f}ms")
                return result
                
        except Exception as e:
            total_time = (asyncio.get_event_loop().time() - start_time) * 1000
            logger.error(f"端到端处理失败: {operation_id}, {e}")
            
            return OrchestrationResult(
                operation_id=operation_id,
                document_id=request.source_path,
                status=ProcessingStatus.FAILED,
                chunks_created=0,
                total_processing_time_ms=total_time,
                error_message=str(e),
                steps_completed=[],
                metadata={"orchestrator": self.orchestrator_name}
            )
    
    async def search_documents(self, request: SearchRequest) -> SearchResult:
        """搜索文档"""
        try:
            if not self.search_backend:
                raise OrchestrationError(
                    "搜索后端未配置",
                    operation="search_documents",
                    error_code="NO_SEARCH_BACKEND"
                )
            
            logger.debug(f"执行搜索: query='{request.query}', limit={request.limit}")
            
            # 调用搜索后端
            # 这里应该调用实际的搜索后端
            # 目前返回模拟结果
            
            mock_chunks = []
            if hasattr(self, '_chunk_cache'):
                for chunks in self._chunk_cache.values():
                    for chunk in chunks:
                        if request.query.lower() in chunk.content.lower():
                            mock_chunks.append(chunk)
                        if len(mock_chunks) >= request.limit:
                            break
                    if len(mock_chunks) >= request.limit:
                        break
            
            # 计算相关性分数（模拟）
            for chunk in mock_chunks:
                # 简单的相关性计算
                query_words = set(request.query.lower().split())
                chunk_words = set(chunk.content.lower().split())
                intersection = len(query_words.intersection(chunk_words))
                union = len(query_words.union(chunk_words))
                chunk.metadata["relevance_score"] = intersection / union if union > 0 else 0.0
            
            # 按相关性排序
            mock_chunks.sort(key=lambda x: x.metadata.get("relevance_score", 0), reverse=True)
            
            result = SearchResult(
                query=request.query,
                chunks=mock_chunks[:request.limit],
                total_results=len(mock_chunks),
                search_time_ms=10.0,  # 模拟搜索时间
                metadata={
                    "search_backend": "mock",
                    "orchestrator": self.orchestrator_name
                }
            )
            
            logger.info(f"搜索完成: 找到 {len(result.chunks)} 个结果")
            return result
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise OrchestrationError(
                f"搜索失败: {str(e)}",
                operation="search_documents",
                error_code="SEARCH_FAILED",
                original_error=e
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "orchestrator": {
                "name": self.orchestrator_name,
                "status": "healthy",
                "cached_documents": len(self._document_cache) if self.enable_caching else 0
            }
        }
        
        # 检查文件加载器
        try:
            if hasattr(self.file_loader, 'health_check'):
                health_status["file_loader"] = await self.file_loader.health_check()
            else:
                health_status["file_loader"] = {
                    "name": self.file_loader.loader_name,
                    "status": "healthy"
                }
        except Exception as e:
            health_status["file_loader"] = {
                "status": "error",
                "error": str(e)
            }
        
        # 检查文档处理器
        try:
            if hasattr(self.document_processor, 'health_check'):
                health_status["document_processor"] = await self.document_processor.health_check()
            else:
                health_status["document_processor"] = {
                    "name": self.document_processor.processor_name,
                    "status": "healthy"
                }
        except Exception as e:
            health_status["document_processor"] = {
                "status": "error", 
                "error": str(e)
            }
        
        # 检查存储后端
        if self.storage_backend:
            try:
                if hasattr(self.storage_backend, 'health_check'):
                    health_status["storage_backend"] = await self.storage_backend.health_check()
                else:
                    health_status["storage_backend"] = {"status": "healthy"}
            except Exception as e:
                health_status["storage_backend"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            health_status["storage_backend"] = {"status": "not_configured"}
        
        # 检查搜索后端
        if self.search_backend:
            try:
                if hasattr(self.search_backend, 'health_check'):
                    health_status["search_backend"] = await self.search_backend.health_check()
                else:
                    health_status["search_backend"] = {"status": "healthy"}
            except Exception as e:
                health_status["search_backend"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            health_status["search_backend"] = {"status": "not_configured"}
        
        # 计算整体状态
        all_healthy = all(
            component.get("status") == "healthy" 
            for component in health_status.values()
            if isinstance(component, dict) and component.get("status") != "not_configured"
        )
        
        health_status["overall_status"] = "healthy" if all_healthy else "degraded"
        health_status["timestamp"] = datetime.utcnow().isoformat()
        
        return health_status
    
    async def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """根据ID获取文档"""
        try:
            # 先从缓存查找
            if self.enable_caching and document_id in self._document_cache:
                return self._document_cache[document_id]
            
            # 从存储后端查找
            if self.storage_backend:
                # 这里应该调用存储后端的查询方法
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"获取文档失败 {document_id}: {e}")
            return None
    
    async def get_chunks_by_document_id(self, document_id: str) -> List[DocumentChunk]:
        """根据文档ID获取所有块"""
        try:
            # 先从缓存查找
            if self.enable_caching and document_id in self._chunk_cache:
                return self._chunk_cache[document_id]
            
            # 从存储后端查找
            if self.storage_backend:
                # 这里应该调用存储后端的查询方法
                pass
            
            return []
            
        except Exception as e:
            logger.error(f"获取文档块失败 {document_id}: {e}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档及其相关数据"""
        try:
            # 从缓存删除
            if self.enable_caching:
                self._document_cache.pop(document_id, None)
                self._chunk_cache.pop(document_id, None)
            
            # 从存储后端删除
            if self.storage_backend:
                # 这里应该调用存储后端的删除方法
                pass
            
            # 从搜索索引删除
            if self.search_backend:
                # 这里应该调用搜索后端的删除方法
                pass
            
            logger.info(f"文档删除成功: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败 {document_id}: {e}")
            return False
    
    async def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """更新文档元数据"""
        try:
            # 更新缓存中的元数据
            if self.enable_caching and document_id in self._document_cache:
                document = self._document_cache[document_id]
                document.metadata.update(metadata)
            
            # 更新存储后端中的元数据
            if self.storage_backend:
                # 这里应该调用存储后端的更新方法
                pass
            
            logger.info(f"文档元数据更新成功: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新文档元数据失败 {document_id}: {e}")
            return False
    
    async def _load_file(self, request: OrchestrationRequest) -> Document:
        """加载文件"""
        try:
            from ..models import FileLoadRequest
            
            # 创建FileLoadRequest对象
            file_request = FileLoadRequest(
                file_path=request.source_path,
                metadata=request.metadata or {}
            )
            
            document = await self.file_loader.load_document(file_request)
            
            if not document:
                raise OrchestrationError(
                    f"文件加载失败: {request.source_path}",
                    operation="load_file",
                    error_code="FILE_LOAD_FAILED"
                )
            
            return document
            
        except Exception as e:
            logger.error(f"文件加载失败: {e}")
            raise OrchestrationError(
                f"文件加载失败: {str(e)}",
                operation="load_file", 
                error_code="FILE_LOAD_ERROR",
                original_error=e
            )
    
    async def _process_document(self, request: ProcessingRequest) -> ProcessingResult:
        """处理文档"""
        try:
            result = await self.document_processor.process_document(request)
            
            if result.status != ProcessingStatus.COMPLETED:
                raise OrchestrationError(
                    f"文档处理失败: {result.error_message}",
                    operation="process_document",
                    error_code="DOCUMENT_PROCESSING_FAILED"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            raise OrchestrationError(
                f"文档处理失败: {str(e)}",
                operation="process_document",
                error_code="DOCUMENT_PROCESSING_ERROR",
                original_error=e
            )
    
    async def _store_document_data(self, document: Document, chunks: List[DocumentChunk]) -> None:
        """存储文档数据"""
        try:
            # 这里应该调用存储后端的存储方法
            # 目前只是模拟
            logger.debug(f"存储文档 {document.id} 和 {len(chunks)} 个块")
            await asyncio.sleep(0.1)  # 模拟存储时间
            
        except Exception as e:
            logger.error(f"存储文档数据失败: {e}")
            raise OrchestrationError(
                f"存储失败: {str(e)}",
                operation="store_document_data",
                error_code="STORAGE_ERROR",
                original_error=e
            )
    
    async def _build_search_index(self, chunks: List[DocumentChunk]) -> None:
        """构建搜索索引"""
        try:
            # 这里应该调用搜索后端的索引构建方法
            # 目前只是模拟
            logger.debug(f"为 {len(chunks)} 个块构建搜索索引")
            await asyncio.sleep(0.1)  # 模拟索引构建时间
            
        except Exception as e:
            logger.error(f"构建搜索索引失败: {e}")
            raise OrchestrationError(
                f"索引构建失败: {str(e)}",
                operation="build_search_index",
                error_code="INDEX_BUILD_ERROR", 
                original_error=e
            )
