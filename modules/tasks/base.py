"""
异步任务处理模块接口定义

定义异步任务服务和任务处理器的标准接口，支持Celery等多种后端实现。
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    SUCCESS = "success"  # 执行成功
    FAILURE = "failure"  # 执行失败
    RETRY = "retry"  # 重试中
    REVOKED = "revoked"  # 已取消


class TaskPriority(Enum):
    """任务优先级枚举"""

    LOW = 1  # 低优先级
    NORMAL = 5  # 普通优先级
    HIGH = 8  # 高优先级
    CRITICAL = 10  # 关键优先级


class TaskConfig:
    """任务配置"""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: int = 60,
        timeout: Optional[int] = None,
        expires: Optional[int] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        queue: Optional[str] = None,
        **kwargs,
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay  # 重试延迟(秒)
        self.timeout = timeout  # 超时时间(秒)
        self.expires = expires  # 过期时间(秒)
        self.priority = priority
        self.queue = queue  # 指定队列
        self.extra_options = kwargs


class TaskResult:
    """任务执行结果"""

    def __init__(
        self,
        task_id: str,
        status: TaskStatus,
        result: Any = None,
        error: Optional[str] = None,
        traceback: Optional[str] = None,
        retries: int = 0,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.status = status
        self.result = result
        self.error = error
        self.traceback = traceback
        self.retries = retries
        self.started_at = started_at
        self.completed_at = completed_at
        self.metadata = metadata or {}

    @property
    def processing_time(self) -> Optional[float]:
        """计算处理时间(秒)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_completed(self) -> bool:
        """是否已完成(成功或失败)"""
        return self.status in [TaskStatus.SUCCESS, TaskStatus.FAILURE]

    @property
    def is_success(self) -> bool:
        """是否执行成功"""
        return self.status == TaskStatus.SUCCESS


class TaskProgress:
    """任务进度信息"""

    def __init__(
        self,
        task_id: str,
        current: int = 0,
        total: int = 100,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.current = current
        self.total = total
        self.description = description
        self.metadata = metadata or {}
        self.updated_at = datetime.utcnow()

    @property
    def percentage(self) -> float:
        """进度百分比"""
        if self.total == 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100)


class TaskError(Exception):
    """任务处理错误基类"""

    def __init__(
        self,
        message: str,
        task_name: Optional[str] = None,
        task_id: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        self.task_name = task_name
        self.task_id = task_id
        self.error_code = error_code
        super().__init__(message)


class TaskTimeoutError(TaskError):
    """任务超时错误"""

    pass


class TaskRetryError(TaskError):
    """任务重试错误"""

    pass


class ITaskHandler(ABC):
    """任务处理器接口"""

    @abstractmethod
    async def handle(self, *args, **kwargs) -> Any:
        """
        处理任务

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Any: 任务处理结果

        Raises:
            TaskError: 任务处理失败时抛出
        """
        pass

    @property
    @abstractmethod
    def task_name(self) -> str:
        """
        获取任务名称

        Returns:
            str: 唯一的任务名称标识
        """
        pass

    @property
    def task_config(self) -> TaskConfig:
        """
        获取任务配置

        Returns:
            TaskConfig: 任务配置，可重写以自定义配置
        """
        return TaskConfig()

    async def on_success(self, task_id: str, result: Any, **kwargs) -> None:
        """
        任务成功回调

        Args:
            task_id: 任务ID
            result: 任务结果
            **kwargs: 额外参数
        """
        pass

    async def on_failure(self, task_id: str, error: Exception, **kwargs) -> None:
        """
        任务失败回调

        Args:
            task_id: 任务ID
            error: 异常信息
            **kwargs: 额外参数
        """
        pass

    async def on_retry(
        self, task_id: str, error: Exception, retry_count: int, **kwargs
    ) -> None:
        """
        任务重试回调

        Args:
            task_id: 任务ID
            error: 引发重试的异常
            retry_count: 重试次数
            **kwargs: 额外参数
        """
        pass


class ITaskService(ABC):
    """异步任务服务接口"""

    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化任务服务

        Raises:
            TaskError: 初始化失败时抛出
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理任务服务资源"""
        pass

    @abstractmethod
    async def submit_task(
        self,
        task_name: str,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        delay: Optional[int] = None,
        eta: Optional[datetime] = None,
        config: Optional[TaskConfig] = None,
        **kwargs,
    ) -> str:
        """
        提交异步任务

        Args:
            task_name: 任务名称
            *args: 任务参数
            priority: 任务优先级
            delay: 延迟执行时间(秒)
            eta: 预计执行时间
            config: 任务配置
            **kwargs: 任务关键字参数

        Returns:
            str: 任务ID

        Raises:
            TaskError: 提交失败时抛出
        """
        pass

    @abstractmethod
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """
        获取任务结果

        Args:
            task_id: 任务ID

        Returns:
            Optional[TaskResult]: 任务结果，不存在时返回None
        """
        pass

    @abstractmethod
    async def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """
        获取任务进度

        Args:
            task_id: 任务ID

        Returns:
            Optional[TaskProgress]: 任务进度，不存在时返回None
        """
        pass

    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 取消是否成功
        """
        pass

    @abstractmethod
    async def retry_task(self, task_id: str) -> str:
        """
        重试任务

        Args:
            task_id: 原任务ID

        Returns:
            str: 新任务ID

        Raises:
            TaskError: 重试失败时抛出
        """
        pass

    @abstractmethod
    async def list_active_tasks(self) -> List[str]:
        """
        列出活跃任务

        Returns:
            List[str]: 活跃任务ID列表
        """
        pass

    @abstractmethod
    async def get_task_stats(self) -> Dict[str, Any]:
        """
        获取任务统计信息

        Returns:
            Dict[str, Any]: 任务统计数据
        """
        pass

    @abstractmethod
    def register_handler(self, handler: ITaskHandler) -> None:
        """
        注册任务处理器

        Args:
            handler: 任务处理器实例

        Raises:
            TaskError: 注册失败时抛出
        """
        pass

    @abstractmethod
    def unregister_handler(self, task_name: str) -> bool:
        """
        注销任务处理器

        Args:
            task_name: 任务名称

        Returns:
            bool: 注销是否成功
        """
        pass

    @abstractmethod
    def is_handler_registered(self, task_name: str) -> bool:
        """
        检查任务处理器是否已注册

        Args:
            task_name: 任务名称

        Returns:
            bool: 是否已注册
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        pass

    @property
    @abstractmethod
    def service_name(self) -> str:
        """
        获取服务名称

        Returns:
            str: 服务名称
        """
        pass


class ITaskRegistry(ABC):
    """任务注册表接口"""

    @abstractmethod
    def register(self, task_name: str, handler: ITaskHandler) -> None:
        """
        注册任务处理器

        Args:
            task_name: 任务名称
            handler: 任务处理器
        """
        pass

    @abstractmethod
    def unregister(self, task_name: str) -> bool:
        """
        注销任务处理器

        Args:
            task_name: 任务名称

        Returns:
            bool: 注销是否成功
        """
        pass

    @abstractmethod
    def get_handler(self, task_name: str) -> Optional[ITaskHandler]:
        """
        获取任务处理器

        Args:
            task_name: 任务名称

        Returns:
            Optional[ITaskHandler]: 处理器实例
        """
        pass

    @abstractmethod
    def list_tasks(self) -> List[str]:
        """
        列出所有已注册任务

        Returns:
            List[str]: 任务名称列表
        """
        pass

    @abstractmethod
    def is_registered(self, task_name: str) -> bool:
        """
        检查任务是否已注册

        Args:
            task_name: 任务名称

        Returns:
            bool: 是否已注册
        """
        pass


# 任务处理器装饰器接口类型
TaskHandlerDecorator = Callable[[type], type]
