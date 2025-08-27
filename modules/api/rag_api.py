"""
RAG API 实现

提供统一的RAG系统API接口，支持文档处理、搜索和管理功能。
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from modules.api.base import APIError, IModularAPI
from modules.file_loader import MultiFormatFileLoader
from modules.models import (
    ChunkingStrategy,
    OrchestrationRequest,
    ProcessingStatus,
    SearchRequest,
)
from modules.orchestrator import DocumentOrchestrator
from modules.processors import ChunkingProcessor

logger = logging.getLogger(__name__)


class RagAPI(IModularAPI):
    """RAG API主实现类

    提供文档处理、搜索、管理等完整的RAG功能接口。
    """

    def __init__(
        self,
        orchestrator: Optional[DocumentOrchestrator] = None,
        enable_caching: bool = True,
        default_chunk_size: int = 1000,
        default_chunk_overlap: int = 200,
    ):
        """
        初始化简单API

        Args:
            orchestrator: 文档编排器（可选，会自动创建）
            enable_caching: 是否启用缓存
            default_chunk_size: 默认块大小
            default_chunk_overlap: 默认重叠大小
        """
        self.enable_caching = enable_caching
        self.default_chunk_size = default_chunk_size
        self.default_chunk_overlap = default_chunk_overlap

        # 初始化组件
        if orchestrator is None:
            file_loader = MultiFormatFileLoader()
            document_processor = ChunkingProcessor(
                default_chunk_size=default_chunk_size,
                default_overlap=default_chunk_overlap,
            )
            self.orchestrator = DocumentOrchestrator(
                file_loader=file_loader,
                document_processor=document_processor,
                enable_caching=enable_caching,
            )
        else:
            self.orchestrator = orchestrator

        # API状态
        self._initialized = False

        logger.info("RagAPI 初始化完成")

    async def initialize(self) -> None:
        """初始化API"""
        if not self._initialized:
            # 这里可以添加初始化逻辑
            self._initialized = True
            logger.info("RagAPI 已初始化")

    async def process_file(self, file_path: str, **options) -> Dict[str, Any]:
        """
        处理单个文件

        Args:
            file_path: 文件路径
            **options: 处理选项，包括：
                - chunking_strategy: 分块策略（'fixed_size', 'semantic', 'paragraph', 'sentence'）
                - chunk_size: 块大小
                - chunk_overlap: 重叠大小
                - generate_embeddings: 是否生成嵌入向量
                - metadata: 额外元数据

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            await self.initialize()

            # 解析选项
            chunking_strategy_str = options.get("chunking_strategy", "fixed_size")
            chunking_strategy = self._parse_chunking_strategy(chunking_strategy_str)

            chunk_size = options.get("chunk_size", self.default_chunk_size)
            chunk_overlap = options.get("chunk_overlap", self.default_chunk_overlap)
            generate_embeddings = options.get("generate_embeddings", False)
            metadata = options.get("metadata", {})

            # 创建编排请求
            request = OrchestrationRequest(
                source_path=file_path,
                chunking_strategy=chunking_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                generate_embeddings=generate_embeddings,
                metadata=metadata,
            )

            # 执行处理
            result = await self.orchestrator.process_document_end_to_end(request)

            # 转换为API响应格式
            response = {
                "success": result.status == ProcessingStatus.COMPLETED,
                "document_id": result.document_id,
                "operation_id": result.operation_id,
                "chunks_created": result.chunks_created,
                "processing_time_ms": result.total_processing_time_ms,
                "metadata": result.metadata or {},
            }

            if result.error_message:
                response["error"] = result.error_message

            return response

        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
            raise APIError(
                f"处理文件失败: {str(e)}",
                error_code="PROCESS_FILE_FAILED",
                status_code=500,
                details={"file_path": file_path},
            )

    async def process_files(
        self, file_paths: List[str], **options
    ) -> List[Dict[str, Any]]:
        """批量处理文件"""
        try:
            await self.initialize()

            results = []

            # 并发处理（有限制）
            max_concurrent = options.get("max_concurrent", 3)
            semaphore = asyncio.Semaphore(max_concurrent)

            async def process_single_file(file_path: str) -> Dict[str, Any]:
                async with semaphore:
                    try:
                        return await self.process_file(file_path, **options)
                    except APIError as e:
                        return {
                            "success": False,
                            "file_path": file_path,
                            "error": str(e),
                            "error_code": e.error_code,
                        }

            # 创建任务
            tasks = [process_single_file(fp) for fp in file_paths]

            # 等待所有任务完成
            results = await asyncio.gather(*tasks)

            return results

        except Exception as e:
            logger.error(f"批量处理文件失败: {e}")
            raise APIError(
                f"批量处理失败: {str(e)}",
                error_code="BATCH_PROCESS_FAILED",
                status_code=500,
                details={"file_count": len(file_paths)},
            )

    async def search(self, query: str, limit: int = 10, **filters) -> Dict[str, Any]:
        """搜索文档"""
        try:
            await self.initialize()

            # 创建搜索请求
            search_request = SearchRequest(query=query, limit=limit, filters=filters)

            # 执行搜索
            result = await self.orchestrator.search_documents(search_request)

            # 转换为API响应格式
            response = {
                "query": result.query,
                "results": [
                    {
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "content": chunk.content,
                        "score": chunk.metadata.get("relevance_score", 0.0),
                        "metadata": chunk.metadata,
                    }
                    for chunk in result.chunks
                ],
                "total_results": result.total_results,
                "search_time_ms": result.search_time_ms,
                "metadata": result.metadata or {},
            }

            return response

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise APIError(
                f"搜索失败: {str(e)}",
                error_code="SEARCH_FAILED",
                status_code=500,
                details={"query": query},
            )

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取文档"""
        try:
            await self.initialize()

            document = await self.orchestrator.get_document_by_id(document_id)

            if not document:
                return None

            return {
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "content_type": document.content_type.value,
                "source_path": document.source_path,
                "file_size": document.file_size,
                "created_at": (
                    document.created_at.isoformat() if document.created_at else None
                ),
                "updated_at": (
                    document.updated_at.isoformat() if document.updated_at else None
                ),
                "metadata": document.metadata,
                "tags": document.tags,
            }

        except Exception as e:
            logger.error(f"获取文档失败 {document_id}: {e}")
            raise APIError(
                f"获取文档失败: {str(e)}",
                error_code="GET_DOCUMENT_FAILED",
                status_code=500,
                details={"document_id": document_id},
            )

    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """获取文档块"""
        try:
            await self.initialize()

            chunks = await self.orchestrator.get_chunks_by_document_id(document_id)

            return [
                {
                    "id": chunk.id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "start_position": chunk.start_position,
                    "end_position": chunk.end_position,
                    "chunk_size": chunk.chunk_size,
                    "strategy": (
                        chunk.strategy.value
                        if hasattr(chunk, "strategy")
                        else "unknown"
                    ),
                    "metadata": chunk.metadata,
                }
                for chunk in chunks
            ]

        except Exception as e:
            logger.error(f"获取文档块失败 {document_id}: {e}")
            raise APIError(
                f"获取文档块失败: {str(e)}",
                error_code="GET_CHUNKS_FAILED",
                status_code=500,
                details={"document_id": document_id},
            )

    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            await self.initialize()

            success = await self.orchestrator.delete_document(document_id)

            if success:
                logger.info(f"文档删除成功: {document_id}")
            else:
                logger.warning(f"文档删除失败: {document_id}")

            return success

        except Exception as e:
            logger.error(f"删除文档失败 {document_id}: {e}")
            raise APIError(
                f"删除文档失败: {str(e)}",
                error_code="DELETE_DOCUMENT_FAILED",
                status_code=500,
                details={"document_id": document_id},
            )

    async def update_document_metadata(
        self, document_id: str, metadata: Dict[str, Any]
    ) -> bool:
        """更新文档元数据"""
        try:
            await self.initialize()

            success = await self.orchestrator.update_document_metadata(
                document_id, metadata
            )

            if success:
                logger.info(f"文档元数据更新成功: {document_id}")
            else:
                logger.warning(f"文档元数据更新失败: {document_id}")

            return success

        except Exception as e:
            logger.error(f"更新文档元数据失败 {document_id}: {e}")
            raise APIError(
                f"更新文档元数据失败: {str(e)}",
                error_code="UPDATE_METADATA_FAILED",
                status_code=500,
                details={"document_id": document_id},
            )

    async def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            await self.initialize()

            health_status = await self.orchestrator.health_check()

            # 添加API层状态
            status = {
                "api": {
                    "name": "RagAPI",
                    "initialized": self._initialized,
                    "caching_enabled": self.enable_caching,
                },
                "components": health_status,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return status

        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            raise APIError(
                f"获取状态失败: {str(e)}",
                error_code="GET_STATUS_FAILED",
                status_code=500,
            )

    async def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        try:
            await self.initialize()

            # 从文件加载器获取支持的格式
            if hasattr(self.orchestrator.file_loader, "supported_formats"):
                formats = await self.orchestrator.file_loader.supported_formats()
            else:
                # 默认支持的格式
                formats = [
                    ".txt",
                    ".pdf",
                    ".doc",
                    ".docx",
                    ".html",
                    ".md",
                    ".json",
                    ".csv",
                ]

            return formats

        except Exception as e:
            logger.error(f"获取支持格式失败: {e}")
            raise APIError(
                f"获取支持格式失败: {str(e)}",
                error_code="GET_FORMATS_FAILED",
                status_code=500,
            )

    def _parse_chunking_strategy(self, strategy_str: str) -> ChunkingStrategy:
        """解析分块策略字符串"""
        strategy_mapping = {
            "fixed_size": ChunkingStrategy.FIXED_SIZE,
            "semantic": ChunkingStrategy.SEMANTIC,
            "paragraph": ChunkingStrategy.PARAGRAPH,
            "sentence": ChunkingStrategy.SENTENCE,
        }

        strategy = strategy_mapping.get(strategy_str.lower())
        if not strategy:
            logger.warning(f"未知的分块策略: {strategy_str}, 使用默认策略")
            return ChunkingStrategy.FIXED_SIZE

        return strategy
