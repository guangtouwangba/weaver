"""
工作流服务层

提供统一的工作流管理接口，支持架构优化后的任务分离设计
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..tasks.orchestrator import TaskDefinition, WorkflowDefinition, orchestrator
from .base_service import BaseService

# Schema imports will be added when needed

logger = logging.getLogger(__name__)


class WorkflowService(BaseService):
    """工作流业务服务"""

    def __init__(self, session: Optional[AsyncSession] = None):
        if session:
            super().__init__(session)
        else:
            # 工作流服务可以独立于数据库session运行
            self.session = None

    async def start_document_processing(
        self,
        file_id: str,
        document_data: Dict[str, Any],
        enable_rag: bool = True,
        topic_id: Optional[int] = None,
        embedding_provider: str = "openai",
        vector_store_provider: str = "weaviate",
        priority: int = 5,
        **metadata,
    ) -> str:
        """
        启动文档处理工作流

        Args:
            file_id: 文件ID
            document_data: 文档数据
            enable_rag: 是否启用RAG处理
            topic_id: 主题ID
            embedding_provider: 嵌入服务提供商
            vector_store_provider: 向量存储提供商
            priority: 优先级
            **metadata: 其他元数据

        Returns:
            str: 工作流执行ID
        """
        try:
            # 准备工作流上下文
            context = {
                "file_id": file_id,
                "document_data": document_data,
                "trigger_rag": enable_rag,
                "topic_id": topic_id,
                "embedding_provider": embedding_provider,
                "vector_store_provider": vector_store_provider,
                "priority": priority,
                "started_by": "workflow_service",
                "metadata": metadata,
            }

            # 启动文档处理工作流
            execution_id = await orchestrator.start_workflow(
                workflow_id="document_processing", context=context
            )

            logger.info(f"文档处理工作流已启动: {execution_id}")
            return execution_id

        except Exception as e:
            logger.error(f"启动文档处理工作流失败: {e}")
            raise

    async def create_document_only(
        self, file_id: str, document_data: Dict[str, Any], **metadata
    ) -> Dict[str, Any]:
        """
        仅创建文档，不进行RAG处理

        Args:
            file_id: 文件ID
            document_data: 文档数据
            **metadata: 其他元数据

        Returns:
            Dict[str, Any]: 创建结果
        """
        try:
            from celery import current_app

            # 直接调用文档创建任务
            task = current_app.send_task(
                "document.create",
                kwargs={
                    "file_id": file_id,
                    "document_data": document_data,
                    "trigger_rag": False,
                    **metadata,
                },
                queue="document_queue",
                priority=8,
            )

            logger.info(f"文档创建任务已提交: {task.id}")

            return {
                "task_id": task.id,
                "task_type": "document.create",
                "submitted_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"提交文档创建任务失败: {e}")
            raise

    async def process_rag_only(
        self,
        document_id: str,
        file_path: str,
        content_type: str = "txt",
        topic_id: Optional[int] = None,
        embedding_provider: str = "openai",
        vector_store_provider: str = "weaviate",
        **metadata,
    ) -> Dict[str, Any]:
        """
        仅进行RAG处理，假设文档已存在

        Args:
            document_id: 文档ID
            file_path: 文件路径
            content_type: 内容类型
            topic_id: 主题ID
            embedding_provider: 嵌入服务提供商
            vector_store_provider: 向量存储提供商
            **metadata: 其他元数据

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            from celery import current_app

            # 直接调用RAG处理任务
            task = current_app.send_task(
                "rag.process_document_async",
                kwargs={
                    "document_id": document_id,
                    "file_path": file_path,
                    "content_type": content_type,
                    "topic_id": topic_id,
                    "embedding_provider": embedding_provider,
                    "vector_store_provider": vector_store_provider,
                    "orchestrated": False,
                    **metadata,
                },
                queue="rag_queue",
                priority=5,
            )

            logger.info(f"RAG处理任务已提交: {task.id}")

            return {
                "task_id": task.id,
                "task_type": "rag.process_document_async",
                "submitted_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"提交RAG处理任务失败: {e}")
            raise

    async def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流执行状态

        Args:
            execution_id: 工作流执行ID

        Returns:
            Optional[Dict[str, Any]]: 执行状态
        """
        try:
            status = orchestrator.get_execution_status(execution_id)
            return status
        except Exception as e:
            logger.error(f"获取工作流状态失败: {execution_id}, {e}")
            return None

    async def cancel_workflow(self, execution_id: str, reason: str = None) -> bool:
        """
        取消工作流执行

        Args:
            execution_id: 工作流执行ID
            reason: 取消原因

        Returns:
            bool: 是否成功取消
        """
        try:
            success = orchestrator.cancel_execution(execution_id)
            if success:
                logger.info(f"工作流已取消: {execution_id}, 原因: {reason}")
            return success
        except Exception as e:
            logger.error(f"取消工作流失败: {execution_id}, {e}")
            return False

    async def register_custom_workflow(self, workflow_def: WorkflowDefinition):
        """
        注册自定义工作流

        Args:
            workflow_def: 工作流定义
        """
        try:
            orchestrator.register_workflow(workflow_def)
            logger.info(f"自定义工作流已注册: {workflow_def.workflow_id}")
        except Exception as e:
            logger.error(f"注册自定义工作流失败: {workflow_def.workflow_id}, {e}")
            raise

    async def add_workflow_callback(self, execution_id: str, callback: Callable):
        """
        添加工作流状态变更回调

        Args:
            execution_id: 工作流执行ID
            callback: 回调函数
        """
        try:
            orchestrator.add_status_callback(execution_id, callback)
            logger.info(f"工作流回调已添加: {execution_id}")
        except Exception as e:
            logger.error(f"添加工作流回调失败: {execution_id}, {e}")
            raise

    async def get_available_workflows(self) -> List[Dict[str, str]]:
        """
        获取可用的工作流列表

        Returns:
            List[Dict[str, str]]: 工作流列表
        """
        try:
            workflows = []
            for workflow_id, workflow_def in orchestrator.workflows.items():
                workflows.append(
                    {
                        "workflow_id": workflow_id,
                        "name": workflow_def.name,
                        "description": workflow_def.description,
                        "task_count": len(workflow_def.tasks),
                    }
                )
            return workflows
        except Exception as e:
            logger.error(f"获取工作流列表失败: {e}")
            return []

    async def get_workflow_definition(
        self, workflow_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取工作流定义详情

        Args:
            workflow_id: 工作流ID

        Returns:
            Optional[Dict[str, Any]]: 工作流定义
        """
        try:
            if workflow_id in orchestrator.workflows:
                workflow_def = orchestrator.workflows[workflow_id]
                return {
                    "workflow_id": workflow_def.workflow_id,
                    "name": workflow_def.name,
                    "description": workflow_def.description,
                    "tasks": [
                        {
                            "task_name": task.task_name,
                            "queue": task.queue,
                            "priority": task.priority,
                            "max_retries": task.max_retries,
                            "timeout": task.timeout,
                            "depends_on": task.depends_on,
                        }
                        for task in workflow_def.tasks
                    ],
                    "dependencies": workflow_def.get_task_dependencies(),
                }
            return None
        except Exception as e:
            logger.error(f"获取工作流定义失败: {workflow_id}, {e}")
            return None


def create_workflow_service(session: Optional[AsyncSession] = None) -> WorkflowService:
    """创建工作流服务实例"""
    return WorkflowService(session=session)


# 便利函数
async def start_document_processing_workflow(
    file_id: str, document_data: Dict[str, Any], **kwargs
) -> str:
    """便利函数：启动文档处理工作流"""
    service = create_workflow_service()
    return await service.start_document_processing(file_id, document_data, **kwargs)


async def get_workflow_status(execution_id: str) -> Optional[Dict[str, Any]]:
    """便利函数：获取工作流状态"""
    service = create_workflow_service()
    return await service.get_workflow_status(execution_id)


async def cancel_workflow(execution_id: str, reason: str = None) -> bool:
    """便利函数：取消工作流"""
    service = create_workflow_service()
    return await service.cancel_workflow(execution_id, reason)


logger.info("工作流服务模块已加载")
