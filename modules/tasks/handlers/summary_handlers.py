"""
Summary Task Handlers

摘要任务处理器，负责处理文档摘要生成和相关任务。
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from logging_system import get_logger, log_execution_time, log_errors, task_context
from modules.tasks.base import ITaskHandler, TaskPriority
from modules.services.task_service import task_handler, register_task_handler
from modules.schemas import TaskName

logger = get_logger(__name__)


@task_handler(
    TaskName.SUMMARY_GENERATE_DOCUMENT.value,
    priority=TaskPriority.NORMAL,
    max_retries=2,
    timeout=300,
    queue="summary_queue",
)
@register_task_handler
class DocumentSummaryHandler(ITaskHandler):
    """文档摘要生成任务处理器"""

    @property
    def task_name(self) -> str:
        return TaskName.SUMMARY_GENERATE_DOCUMENT.value

    @log_execution_time(threshold_ms=1000)
    @log_errors()
    async def handle(
        self,
        document_id: str,
        content: str,
        topic_id: Optional[str] = None,
        file_id: Optional[str] = None,
        force_regenerate: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        生成并存储文档摘要

        Args:
            document_id: 文档ID
            content: 文档内容
            topic_id: 主题ID
            file_id: 文件ID
            force_regenerate: 是否强制重新生成
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            with task_context(
                task_id=f"summary-{document_id}",
                task_name="summary.generate_document",
                queue="summary_queue",
            ):
                logger.info(
                    f"开始文档摘要生成任务: document_id={document_id}, content_length={len(content)}"
                )

                # 验证输入参数
                if not document_id or not content:
                    raise ValueError("document_id和content不能为空")

                if len(content) < 500:
                    logger.warning(f"文档内容太短，跳过摘要生成: {len(content)} < 500")
                    return {
                        "success": False,
                        "error": "content_too_short",
                        "message": f"文档内容太短，无法生成摘要 (长度: {len(content)})",
                        "document_id": document_id,
                    }

                # 初始化摘要服务
                summary_service = await self._create_summary_service()

                # 生成摘要
                summary_doc = await summary_service.generate_document_summary(
                    document_id=document_id,
                    content=content,
                    topic_id=topic_id,
                    force_regenerate=force_regenerate,
                )

                if not summary_doc:
                    raise Exception("摘要生成失败，返回结果为空")

                # 存储摘要到向量数据库
                storage_result = await self._store_summary_to_vector_db(summary_doc)

                # 构建返回结果
                result = {
                    "success": True,
                    "summary_id": summary_doc.id,
                    "summary_content": (
                        summary_doc.summary[:200] + "..."
                        if len(summary_doc.summary) > 200
                        else summary_doc.summary
                    ),
                    "key_topics": summary_doc.key_topics,
                    "document_id": document_id,
                    "topic_id": topic_id,
                    "file_id": file_id,
                    "storage_result": storage_result,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "task_type": "summary.generate_document",
                }

                logger.info(f"文档摘要生成任务完成: {summary_doc.id}")
                return result

        except Exception as e:
            logger.error(f"文档摘要生成任务失败: document_id={document_id}, error={e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "document_id": document_id,
                "topic_id": topic_id,
                "file_id": file_id,
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "task_type": "summary.generate_document",
            }

    async def _create_summary_service(self):
        """创建摘要服务实例"""
        try:
            from modules.services.summary_service import SummaryGenerationService
            from modules.vector_store.weaviate_service import WeaviateVectorStore
            from config.settings import get_config

            config = get_config()

            # 创建向量存储服务
            vector_store = WeaviateVectorStore(
                url=getattr(config, "weaviate_url", None)
                or config.vector_db.weaviate_url
                or "http://localhost:8080",
                api_key=getattr(config, "weaviate_api_key", None),
                create_collections_on_init=True,
            )
            await vector_store.initialize()

            # 创建摘要服务
            # 注意：这里使用None作为session，实际使用时需要传递正确的session
            summary_service = SummaryGenerationService(
                session=None,  # TODO: 需要传递正确的数据库session
                vector_store=vector_store,
            )
            await summary_service.initialize()

            return summary_service

        except Exception as e:
            logger.error(f"摘要服务初始化失败: {e}")
            raise

    async def _store_summary_to_vector_db(self, summary_doc) -> Dict[str, Any]:
        """将摘要存储到向量数据库"""
        try:
            from modules.vector_store.weaviate_service import WeaviateVectorStore
            from config.settings import get_config

            config = get_config()

            # 创建向量存储服务
            vector_store = WeaviateVectorStore(
                url=getattr(config, "weaviate_url", None)
                or config.vector_db.weaviate_url
                or "http://localhost:8080",
                api_key=getattr(config, "weaviate_api_key", None),
                create_collections_on_init=True,
            )
            await vector_store.initialize()

            # 存储摘要
            result = await vector_store.upsert_summary_documents([summary_doc])

            await vector_store.cleanup()

            return {
                "success_count": result.success_count,
                "failed_count": result.failed_count,
                "total_time_ms": result.processing_time_ms,
                "status": "success" if result.failed_count == 0 else "partial_success",
            }

        except Exception as e:
            logger.error(f"摘要向量存储失败: {e}")
            return {
                "success_count": 0,
                "failed_count": 1,
                "total_time_ms": 0,
                "status": "failed",
                "error": str(e),
            }


@task_handler(
    TaskName.SUMMARY_UPDATE_INDEX.value,
    priority=TaskPriority.LOW,
    max_retries=2,
    timeout=120,
    queue="summary_queue",
)
@register_task_handler
class SummaryIndexUpdateHandler(ITaskHandler):
    """摘要索引更新任务处理器"""

    @property
    def task_name(self) -> str:
        return TaskName.SUMMARY_UPDATE_INDEX.value

    @log_execution_time(threshold_ms=500)
    @log_errors()
    async def handle(
        self, summary_id: str, update_type: str = "refresh", **kwargs
    ) -> Dict[str, Any]:
        """
        更新摘要索引

        Args:
            summary_id: 摘要ID
            update_type: 更新类型 (refresh, delete, recreate)
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            with task_context(
                task_id=f"summary-update-{summary_id}",
                task_name="summary.update_index",
                queue="summary_queue",
            ):
                logger.info(
                    f"开始摘要索引更新任务: summary_id={summary_id}, type={update_type}"
                )

                if update_type == "delete":
                    result = await self._delete_summary_from_index(summary_id)
                elif update_type == "recreate":
                    result = await self._recreate_summary_index(summary_id)
                else:  # refresh (default)
                    result = await self._refresh_summary_index(summary_id)

                logger.info(f"摘要索引更新任务完成: {summary_id}")
                return {
                    "success": True,
                    "summary_id": summary_id,
                    "update_type": update_type,
                    "result": result,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }

        except Exception as e:
            logger.error(f"摘要索引更新任务失败: summary_id={summary_id}, error={e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "summary_id": summary_id,
                "update_type": update_type,
                "failed_at": datetime.now(timezone.utc).isoformat(),
            }

    async def _refresh_summary_index(self, summary_id: str) -> Dict[str, Any]:
        """刷新摘要索引"""
        # TODO: 实现摘要索引刷新逻辑
        logger.info(f"刷新摘要索引: {summary_id}")
        return {"action": "refresh", "status": "completed"}

    async def _delete_summary_from_index(self, summary_id: str) -> Dict[str, Any]:
        """从索引中删除摘要"""
        # TODO: 实现摘要删除逻辑
        logger.info(f"删除摘要索引: {summary_id}")
        return {"action": "delete", "status": "completed"}

    async def _recreate_summary_index(self, summary_id: str) -> Dict[str, Any]:
        """重新创建摘要索引"""
        # TODO: 实现摘要索引重建逻辑
        logger.info(f"重建摘要索引: {summary_id}")
        return {"action": "recreate", "status": "completed"}
