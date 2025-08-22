"""
任务协调器模块

负责管理和协调多个任务之间的依赖关系、状态跟踪和错误处理
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from celery import current_app

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 执行中
    SUCCESS = "success"  # 成功完成
    FAILED = "failed"  # 执行失败
    RETRYING = "retrying"  # 重试中
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"  # 超时


class WorkflowStatus(Enum):
    """工作流状态枚举"""

    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskDefinition:
    """任务定义"""

    task_name: str
    queue: str = "default"
    priority: int = 5
    max_retries: int = 3
    timeout: int = 300
    depends_on: List[str] = None

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


@dataclass
class TaskExecution:
    """任务执行状态"""

    task_id: str
    task_name: str
    status: TaskStatus
    celery_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 处理日期时间序列化
        if self.started_at:
            data["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        data["status"] = self.status.value
        return data


@dataclass
class WorkflowDefinition:
    """工作流定义"""

    workflow_id: str
    name: str
    description: str
    tasks: List[TaskDefinition]

    def get_task_dependencies(self) -> Dict[str, List[str]]:
        """获取任务依赖关系图"""
        dependencies = {}
        for task in self.tasks:
            dependencies[task.task_name] = task.depends_on
        return dependencies


@dataclass
class WorkflowExecution:
    """工作流执行状态"""

    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    tasks: Dict[str, TaskExecution] = None
    context: Dict[str, Any] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.tasks is None:
            self.tasks = {}
        if self.context is None:
            self.context = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "context": self.context,
            "error": self.error,
        }


class TaskOrchestrator:
    """任务协调器"""

    def __init__(self):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self._status_callbacks: Dict[str, List[Callable]] = {}

    def register_workflow(self, workflow: WorkflowDefinition):
        """注册工作流定义"""
        self.workflows[workflow.workflow_id] = workflow
        logger.info(f"工作流已注册: {workflow.workflow_id} - {workflow.name}")

    def add_status_callback(self, execution_id: str, callback: Callable):
        """添加状态变更回调"""
        if execution_id not in self._status_callbacks:
            self._status_callbacks[execution_id] = []
        self._status_callbacks[execution_id].append(callback)

    async def start_workflow(self, workflow_id: str, context: Dict[str, Any] = None) -> str:
        """启动工作流执行"""
        if workflow_id not in self.workflows:
            raise ValueError(f"未找到工作流定义: {workflow_id}")

        workflow = self.workflows[workflow_id]
        execution_id = str(uuid4())

        # 创建工作流执行实例
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.INITIALIZED,
            started_at=datetime.utcnow(),
            context=context or {},
        )

        # 初始化任务执行状态
        for task_def in workflow.tasks:
            task_execution = TaskExecution(
                task_id=str(uuid4()), task_name=task_def.task_name, status=TaskStatus.PENDING
            )
            execution.tasks[task_def.task_name] = task_execution

        self.executions[execution_id] = execution
        logger.info(f"工作流执行已启动: {execution_id}")

        # 开始执行工作流
        await self._execute_workflow(execution_id)

        return execution_id

    async def _execute_workflow(self, execution_id: str):
        """执行工作流"""
        execution = self.executions[execution_id]
        workflow = self.workflows[execution.workflow_id]

        execution.status = WorkflowStatus.RUNNING
        await self._notify_status_change(execution_id, "workflow_started")

        try:
            # 获取任务依赖关系
            dependencies = workflow.get_task_dependencies()

            # 执行任务（按依赖关系排序）
            executed_tasks = set()

            while len(executed_tasks) < len(workflow.tasks):
                # 找到可以执行的任务（依赖已满足）
                ready_tasks = []
                for task_def in workflow.tasks:
                    if task_def.task_name in executed_tasks:
                        continue

                    # 检查依赖是否已完成
                    dependencies_met = all(
                        dep in executed_tasks and execution.tasks[dep].status == TaskStatus.SUCCESS
                        for dep in task_def.depends_on
                    )

                    if dependencies_met:
                        ready_tasks.append(task_def)

                if not ready_tasks:
                    # 没有可执行的任务，检查是否有失败的任务
                    failed_tasks = [
                        task_name
                        for task_name, task_exec in execution.tasks.items()
                        if task_exec.status == TaskStatus.FAILED
                    ]
                    if failed_tasks:
                        raise Exception(f"任务失败导致工作流无法继续: {failed_tasks}")
                    else:
                        raise Exception("工作流陷入死锁，没有可执行的任务")

                # 并行执行准备好的任务
                for task_def in ready_tasks:
                    await self._execute_task(execution_id, task_def)
                    executed_tasks.add(task_def.task_name)

            # 所有任务完成
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            await self._notify_status_change(execution_id, "workflow_completed")

            logger.info(f"工作流执行完成: {execution_id}")

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            await self._notify_status_change(execution_id, "workflow_failed")

            logger.error(f"工作流执行失败: {execution_id}, {e}")

    async def _execute_task(self, execution_id: str, task_def: TaskDefinition):
        """执行单个任务"""
        execution = self.executions[execution_id]
        task_execution = execution.tasks[task_def.task_name]

        logger.info(f"开始执行任务: {task_def.task_name}")

        try:
            # 更新任务状态
            task_execution.status = TaskStatus.RUNNING
            task_execution.started_at = datetime.utcnow()
            await self._notify_status_change(execution_id, f"task_started:{task_def.task_name}")

            # 准备任务参数（从上下文中获取）
            task_kwargs = self._prepare_task_kwargs(execution, task_def)

            # 提交Celery任务
            celery_task = current_app.send_task(
                task_def.task_name,
                kwargs=task_kwargs,
                queue=task_def.queue,
                priority=task_def.priority,
                countdown=0,
            )

            task_execution.celery_task_id = celery_task.id

            # 等待任务完成（简化实现，实际应该使用callback或polling）
            # 这里使用简单的状态检查
            import asyncio

            timeout_seconds = task_def.timeout
            start_time = datetime.utcnow()

            while True:
                # 检查超时
                if (datetime.utcnow() - start_time).total_seconds() > timeout_seconds:
                    task_execution.status = TaskStatus.TIMEOUT
                    task_execution.error = "任务执行超时"
                    celery_task.revoke(terminate=True)
                    break

                # 检查任务状态
                celery_result = celery_task.result
                if celery_task.ready():
                    if celery_task.successful():
                        task_execution.status = TaskStatus.SUCCESS
                        task_execution.result = celery_result
                        task_execution.completed_at = datetime.utcnow()

                        # 将结果添加到上下文中
                        execution.context[f"{task_def.task_name}_result"] = celery_result

                        logger.info(f"任务执行成功: {task_def.task_name}")
                    else:
                        task_execution.status = TaskStatus.FAILED
                        task_execution.error = str(celery_result)
                        task_execution.completed_at = datetime.utcnow()

                        logger.error(f"任务执行失败: {task_def.task_name}, {celery_result}")
                    break

                # 等待一段时间再检查
                await asyncio.sleep(1)

            await self._notify_status_change(execution_id, f"task_completed:{task_def.task_name}")

        except Exception as e:
            task_execution.status = TaskStatus.FAILED
            task_execution.error = str(e)
            task_execution.completed_at = datetime.utcnow()

            logger.error(f"任务执行异常: {task_def.task_name}, {e}")
            await self._notify_status_change(execution_id, f"task_failed:{task_def.task_name}")

    def _prepare_task_kwargs(
        self, execution: WorkflowExecution, task_def: TaskDefinition
    ) -> Dict[str, Any]:
        """准备任务参数"""
        # 基础参数从上下文中获取
        kwargs = dict(execution.context)

        # 添加任务执行元数据
        kwargs.update(
            {
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "task_name": task_def.task_name,
                "orchestrated": True,
            }
        )

        return kwargs

    async def _notify_status_change(self, execution_id: str, event: str):
        """通知状态变更"""
        if execution_id in self._status_callbacks:
            for callback in self._status_callbacks[execution_id]:
                try:
                    await callback(execution_id, event, self.executions[execution_id])
                except Exception as e:
                    logger.error(f"状态回调执行失败: {e}")

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态"""
        if execution_id not in self.executions:
            return None

        execution = self.executions[execution_id]
        return execution.to_dict()

    def cancel_execution(self, execution_id: str) -> bool:
        """取消工作流执行"""
        if execution_id not in self.executions:
            return False

        execution = self.executions[execution_id]

        # 取消所有运行中的任务
        for task_execution in execution.tasks.values():
            if task_execution.status == TaskStatus.RUNNING and task_execution.celery_task_id:
                try:
                    current_app.control.revoke(task_execution.celery_task_id, terminate=True)
                    task_execution.status = TaskStatus.CANCELLED
                except Exception as e:
                    logger.error(f"取消任务失败: {task_execution.celery_task_id}, {e}")

        execution.status = WorkflowStatus.CANCELLED
        execution.completed_at = datetime.utcnow()

        logger.info(f"工作流执行已取消: {execution_id}")
        return True


# 全局任务协调器实例
orchestrator = TaskOrchestrator()


# 预定义工作流：文档处理流程
DOCUMENT_PROCESSING_WORKFLOW = WorkflowDefinition(
    workflow_id="document_processing",
    name="文档处理工作流",
    description="完整的文档创建和RAG处理流程",
    tasks=[
        TaskDefinition(
            task_name="document.create",
            queue="document_queue",
            priority=8,
            max_retries=3,
            timeout=300,
            depends_on=[],
        ),
        TaskDefinition(
            task_name="rag.process_document_async",
            queue="rag_queue",
            priority=5,
            max_retries=2,
            timeout=600,
            depends_on=["document.create"],
        ),
        TaskDefinition(
            task_name="document.update_metadata",
            queue="document_queue",
            priority=3,
            max_retries=2,
            timeout=60,
            depends_on=["rag.process_document_async"],
        ),
    ],
)

# 注册预定义工作流
orchestrator.register_workflow(DOCUMENT_PROCESSING_WORKFLOW)

logger.info("任务协调器模块已加载")
