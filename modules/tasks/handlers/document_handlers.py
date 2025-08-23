"""
文档处理任务处理器模块

专门处理文档创建相关的任务，与RAG处理完全分离
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from logging_system import task_context
from modules.schemas.enums import ContentType
from modules.services.task_service import register_task_handler, task_handler
from modules.tasks.base import ITaskHandler, TaskPriority
from modules.tasks.decorators import log_execution_time

logger = logging.getLogger(__name__)


@task_handler(
    "document.create",
    priority=TaskPriority.HIGH,
    max_retries=3,
    timeout=300,
    queue="document_queue",
)
@register_task_handler
class DocumentCreateHandler(ITaskHandler):
    """文档创建任务处理器 - 专门负责文档的数据库创建"""

    @property
    def task_name(self) -> str:
        return "document.create"

    @log_execution_time(threshold_ms=1000)
    async def handle(
        self,
        file_id: str,
        document_data: Dict[str, Any],
        trigger_rag: bool = True,
        **metadata,
    ) -> Dict[str, Any]:
        """
        创建文档记录

        Args:
            file_id: 文件ID
            document_data: 文档数据 (title, content, content_type等)
            trigger_rag: 是否触发RAG处理
            **metadata: 其他元数据

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            with task_context(
                task_id=f"doc-create-{file_id}",
                task_name="document.create",
                queue="document_queue",
            ):
                logger.info(f"开始文档创建任务: {file_id}")

                # 使用同步SQLAlchemy创建文档
                document_id = await self._create_document_sync(
                    file_id=file_id, document_data=document_data, metadata=metadata
                )

                logger.info(f"文档创建成功: {document_id}")

                # 根据配置决定是否触发RAG处理
                rag_task_id = None
                if trigger_rag:
                    rag_task_id = await self._trigger_rag_processing(
                        document_id=document_id,
                        file_id=file_id,
                        document_data=document_data,
                        metadata=metadata,
                    )

                return {
                    "success": True,
                    "document_id": document_id,
                    "file_id": file_id,
                    "rag_task_id": rag_task_id,
                    "rag_triggered": bool(rag_task_id),
                    "created_at": datetime.utcnow().isoformat(),
                    "task_type": "document.create",
                }

        except Exception as e:
            logger.error(f"文档创建任务失败: {file_id}, {e}")

            # 记录失败状态
            await self._record_failure(file_id, str(e))

            return {
                "success": False,
                "file_id": file_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.utcnow().isoformat(),
                "task_type": "document.create",
            }

    async def _create_document_sync(
        self, file_id: str, document_data: Dict[str, Any], metadata: Dict[str, Any]
    ) -> str:
        """使用同步SQLAlchemy创建文档记录"""
        import sqlalchemy as sa
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from config import get_config
        from modules.database.models import Document as DocumentModel

        config = get_config()

        # 使用同步SQLAlchemy避免async context问题
        sync_engine = create_engine(
            config.database.url.replace("postgresql+asyncpg", "postgresql+psycopg2"),
            echo=False,
        )

        SessionLocal = sessionmaker(bind=sync_engine)

        with SessionLocal() as session:
            try:
                # 准备文档元数据
                doc_metadata = {
                    "source": "document_create_task",
                    "file_id": file_id,
                    "created_by_task": "document.create",
                    **metadata,
                }

                # 生成文档ID
                document_id = document_data.get("id") or str(uuid4())

                # 创建文档模型
                document_model = DocumentModel(
                    id=document_id,
                    title=document_data.get("title", f"Document from {file_id}"),
                    content=document_data.get("content", ""),
                    content_type=document_data.get("content_type", "txt"),
                    file_id=file_id,
                    file_path=document_data.get("file_path"),
                    file_size=document_data.get("file_size", 0),
                    doc_metadata=doc_metadata,
                )

                session.add(document_model)
                session.commit()

                logger.info(
                    f"文档记录已创建: {document_model.title} (ID: {document_model.id})"
                )
                return str(document_model.id)

            except Exception as e:
                session.rollback()
                raise Exception(f"文档数据库创建失败: {e}")
            finally:
                session.close()
                sync_engine.dispose()

    async def _trigger_rag_processing(
        self,
        document_id: str,
        file_id: str,
        document_data: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> Optional[str]:
        """触发RAG处理任务"""
        try:
            from celery import current_app

            # 提交RAG处理任务
            rag_task = current_app.send_task(
                "rag.process_document_async",
                args=[],
                kwargs={
                    "document_id": document_id,
                    "file_id": file_id,
                    "file_path": document_data.get("file_path"),
                    "content_type": document_data.get("content_type", "txt"),
                    "topic_id": metadata.get("topic_id"),
                    "embedding_provider": metadata.get("embedding_provider", "openai"),
                    "vector_store_provider": metadata.get(
                        "vector_store_provider", "weaviate"
                    ),
                    "triggered_by": "document.create",
                },
                queue="rag_queue",
                priority=2,
            )

            logger.info(f"RAG处理任务已提交: {rag_task.id} for document {document_id}")
            return rag_task.id

        except Exception as e:
            logger.error(f"RAG任务提交失败: {e}")
            # 不抛出异常，允许文档创建成功但RAG处理失败
            return None

    async def _record_failure(self, file_id: str, error_message: str):
        """记录任务失败状态"""
        try:
            # TODO: 记录到任务状态表或缓存中
            logger.error(f"文档创建任务失败记录: {file_id}, {error_message}")
        except Exception as e:
            logger.error(f"记录失败状态时出错: {e}")


@task_handler(
    "document.update_metadata",
    priority=TaskPriority.NORMAL,
    max_retries=2,
    timeout=60,
    queue="document_queue",
)
@register_task_handler
class DocumentMetadataUpdateHandler(ITaskHandler):
    """文档元数据更新任务处理器"""

    @property
    def task_name(self) -> str:
        return "document.update_metadata"

    @log_execution_time(threshold_ms=500)
    async def handle(
        self, document_id: str, metadata_updates: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        """
        更新文档元数据

        Args:
            document_id: 文档ID
            metadata_updates: 要更新的元数据
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            with task_context(
                task_id=f"doc-meta-{document_id}",
                task_name="document.update_metadata",
                queue="document_queue",
            ):
                logger.info(f"开始更新文档元数据: {document_id}")

                await self._update_metadata_sync(document_id, metadata_updates)

                return {
                    "success": True,
                    "document_id": document_id,
                    "updated_fields": list(metadata_updates.keys()),
                    "updated_at": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"文档元数据更新失败: {document_id}, {e}")
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat(),
            }

    async def _update_metadata_sync(
        self, document_id: str, metadata_updates: Dict[str, Any]
    ):
        """使用同步SQLAlchemy更新文档元数据"""
        import sqlalchemy as sa
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from config import get_config
        from modules.database.models import Document as DocumentModel

        config = get_config()

        sync_engine = create_engine(
            config.database.url.replace("postgresql+asyncpg", "postgresql+psycopg2"),
            echo=False,
        )

        SessionLocal = sessionmaker(bind=sync_engine)

        with SessionLocal() as session:
            try:
                # 获取文档
                document = (
                    session.query(DocumentModel)
                    .filter(DocumentModel.id == document_id)
                    .first()
                )

                if not document:
                    raise ValueError(f"文档不存在: {document_id}")

                # 更新元数据
                current_metadata = document.doc_metadata or {}
                current_metadata.update(metadata_updates)
                current_metadata["last_updated"] = datetime.utcnow().isoformat()

                document.doc_metadata = current_metadata
                session.commit()

                logger.info(f"文档元数据已更新: {document_id}")

            except Exception as e:
                session.rollback()
                raise Exception(f"元数据更新失败: {e}")
            finally:
                session.close()
                sync_engine.dispose()


logger.info("文档任务处理器模块已加载")
