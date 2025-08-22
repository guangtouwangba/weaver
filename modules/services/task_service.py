"""
Async taskService implementation

基于Celery实现的异步Task processing服务，提供任务提交、状态跟踪、错误处理等功能。
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from logging_system import get_logger, log_errors, log_execution_time

try:
    from celery import Celery
    from celery.result import AsyncResult

    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

from ..tasks.base import (
    ITaskHandler,
    ITaskRegistry,
    ITaskService,
    TaskConfig,
    TaskError,
    TaskPriority,
    TaskProgress,
    TaskResult,
    TaskStatus,
)

logger = get_logger(__name__)


class TaskRegistry(ITaskRegistry):
    """任务注册表实现"""

    def __init__(self):
        self._handlers: Dict[str, ITaskHandler] = {}
        self._configs: Dict[str, TaskConfig] = {}
        self._lock = asyncio.Lock()

    @log_execution_time(threshold_ms=50)
    def register(self, task_name: str, handler: ITaskHandler) -> None:
        """注册Task processing器"""
        if self.is_registered(task_name):
            logger.warning(f"任务 {task_name} 已存在，将被覆盖")

        self._handlers[task_name] = handler
        self._configs[task_name] = handler.task_config
        logger.info(f"已注册Task processing器: {task_name}")

    def unregister(self, task_name: str) -> bool:
        """注销Task processing器"""
        if task_name in self._handlers:
            del self._handlers[task_name]
            del self._configs[task_name]
            logger.info(f"已注销Task processing器: {task_name}")
            return True
        return False

    def get_handler(self, task_name: str) -> Optional[ITaskHandler]:
        """获取Task processing器"""
        return self._handlers.get(task_name)

    def get_config(self, task_name: str) -> Optional[TaskConfig]:
        """获取任务配置"""
        return self._configs.get(task_name)

    def list_tasks(self) -> List[str]:
        """列出所有已注册任务"""
        return list(self._handlers.keys())

    def is_registered(self, task_name: str) -> bool:
        """检查任务是否已注册"""
        return task_name in self._handlers

    def get_stats(self) -> Dict[str, Any]:
        """获取注册统计信息"""
        return {
            "total_handlers": len(self._handlers),
            "task_names": list(self._handlers.keys()),
            "configs": {
                name: {
                    "max_retries": config.max_retries,
                    "priority": config.priority.value,
                    "timeout": config.timeout,
                    "queue": config.queue,
                }
                for name, config in self._configs.items()
            },
        }


class CeleryTaskService(ITaskService):
    """基于Celery的Async taskService implementation"""

    def __init__(
        self,
        broker_url: str = "redis://localhost:6379/0",
        result_backend: str = "redis://localhost:6379/0",
        app_name: str = "rag_tasks",
        registry: Optional[ITaskRegistry] = None,
        **celery_config,
    ):
        if not CELERY_AVAILABLE:
            raise TaskError(
                "Celery not available. Please install celery: pip install celery[redis]"
            )

        self.broker_url = broker_url
        self.result_backend = result_backend
        self.app_name = app_name

        # 创建Celery应用
        self.app = Celery(app_name)
        self.app.conf.update(
            broker_url=broker_url,
            result_backend=result_backend,
            task_serializer="pickle",
            accept_content=["pickle", "json"],
            result_serializer="pickle",
            timezone="UTC",
            enable_utc=True,
            task_track_started=True,
            task_reject_on_worker_lost=True,
            result_expires=3600,  # 结果保存1小时
            worker_prefetch_multiplier=1,
            task_acks_late=True,
            **celery_config,
        )

        # 任务注册表
        self.registry = registry or TaskRegistry()

        # 内部状态
        self._initialized = False
        self._progress_store: Dict[str, TaskProgress] = {}

        # 设置任务路由
        self._setup_task_routing()

        logger.info(f"CeleryTask service初始化: {app_name}")

    @log_execution_time(threshold_ms=2000)
    @log_errors()
    async def initialize(self) -> None:
        """初始化Task service"""
        if self._initialized:
            return

        try:
            # 测试连接
            await self._test_connection()

            # 导入Task processing器模块以触发装饰器注册
            self._import_task_handlers()

            # 注册内置任务
            self._register_builtin_tasks()

            # 自动注册全局Task processing器
            await auto_register_handlers(self)

            self._initialized = True
            logger.info("CeleryTask service初始化完成")

        except Exception as e:
            logger.error(f"CeleryTask service初始化失败: {e}")
            raise TaskError(f"服务初始化失败: {e}")

    async def cleanup(self) -> None:
        """清理Task service资源"""
        try:
            # 清理进度存储
            self._progress_store.clear()

            # 关闭Celery连接
            if hasattr(self.app, "close"):
                self.app.close()

            self._initialized = False
            logger.info("CeleryTask service资源清理完成")

        except Exception as e:
            logger.error(f"CeleryTask service清理失败: {e}")

    @log_execution_time(threshold_ms=100)
    @log_errors()
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
        """提交Async task"""
        if not self._initialized:
            await self.initialize()

        if not self.is_handler_registered(task_name):
            raise TaskError(f"未注册的任务: {task_name}")

        try:
            # 获取任务配置
            task_config = config or self.registry.get_config(task_name) or TaskConfig()

            # 构建Celery任务选项
            options = {
                "priority": priority.value,
                "retry": task_config.max_retries > 0,
                "retry_policy": {
                    "max_retries": task_config.max_retries,
                    "interval_start": task_config.retry_delay,
                    "interval_step": task_config.retry_delay,
                },
            }

            # 设置延迟或ETA
            if delay:
                options["countdown"] = delay
            elif eta:
                options["eta"] = eta

            # 设置超时
            if task_config.timeout:
                options["time_limit"] = task_config.timeout
                options["soft_time_limit"] = task_config.timeout - 10

            # 设置队列
            if task_config.queue:
                options["queue"] = task_config.queue

            # 设置过期时间
            if task_config.expires:
                options["expires"] = task_config.expires

            # 提交任务
            async_result = self.app.send_task(task_name, args=args, kwargs=kwargs, **options)

            logger.info(f"任务已提交: {task_name} (ID: {async_result.id})")
            return async_result.id

        except Exception as e:
            logger.error(f"任务提交失败: {task_name}, {e}")
            raise TaskError(f"任务提交失败: {e}", task_name=task_name)

    @log_execution_time(threshold_ms=50)
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """获取Task result"""
        try:
            async_result = AsyncResult(task_id, app=self.app)

            # 转换Celery状态到TaskStatus
            status_mapping = {
                "PENDING": TaskStatus.PENDING,
                "STARTED": TaskStatus.RUNNING,
                "SUCCESS": TaskStatus.SUCCESS,
                "FAILURE": TaskStatus.FAILURE,
                "RETRY": TaskStatus.RETRY,
                "REVOKED": TaskStatus.REVOKED,
            }

            status = status_mapping.get(async_result.status, TaskStatus.PENDING)

            # 获取结果和错误信息
            result = None
            error = None
            traceback = None

            if status == TaskStatus.SUCCESS:
                result = async_result.result
            elif status == TaskStatus.FAILURE:
                error = str(async_result.result) if async_result.result else "Unknown error"
                traceback = async_result.traceback

            # 获取任务信息
            info = async_result.info or {}
            retries = info.get("retries", 0)

            # 获取时间信息
            started_at = None
            completed_at = None

            if hasattr(async_result, "date_done") and async_result.date_done:
                completed_at = async_result.date_done

            return TaskResult(
                task_id=task_id,
                status=status,
                result=result,
                error=error,
                traceback=traceback,
                retries=retries,
                started_at=started_at,
                completed_at=completed_at,
                metadata=info,
            )

        except Exception as e:
            logger.error(f"获取Task result失败: {task_id}, {e}")
            return None

    async def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """获取任务进度"""
        # 首先检查内存存储
        if task_id in self._progress_store:
            return self._progress_store[task_id]

        # 尝试从Celery结果中获取进度信息
        try:
            async_result = AsyncResult(task_id, app=self.app)
            if async_result.info and isinstance(async_result.info, dict):
                progress_info = async_result.info.get("progress")
                if progress_info:
                    return TaskProgress(
                        task_id=task_id,
                        current=progress_info.get("current", 0),
                        total=progress_info.get("total", 100),
                        description=progress_info.get("description", ""),
                        metadata=progress_info.get("metadata", {}),
                    )
        except Exception as e:
            logger.debug(f"获取任务进度失败: {task_id}, {e}")

        return None

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            self.app.control.revoke(task_id, terminate=True)
            logger.info(f"任务已取消: {task_id}")
            return True
        except Exception as e:
            logger.error(f"取消Task failure: {task_id}, {e}")
            return False

    async def retry_task(self, task_id: str) -> str:
        """重试任务"""
        # 获取原任务信息
        original_result = await self.get_task_result(task_id)
        if not original_result:
            raise TaskError(f"找不到任务: {task_id}")

        # TODO: 实现Task retry逻辑
        # 这需要存储原始任务参数，当前简化实现
        raise NotImplementedError("Task retry功能待实现")

    async def list_active_tasks(self) -> List[str]:
        """列出活跃任务"""
        try:
            inspect = self.app.control.inspect()
            active_tasks = inspect.active()

            task_ids = []
            if active_tasks:
                for worker, tasks in active_tasks.items():
                    for task in tasks:
                        task_ids.append(task["id"])

            return task_ids
        except Exception as e:
            logger.error(f"获取活跃Task failure: {e}")
            return []

    async def get_task_stats(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            inspect = self.app.control.inspect()

            # 获取活跃任务
            active_tasks = inspect.active() or {}
            active_count = sum(len(tasks) for tasks in active_tasks.values())

            # 获取已注册任务
            registered_tasks = inspect.registered() or {}

            # 获取统计信息
            stats = inspect.stats() or {}

            return {
                "active_tasks": active_count,
                "registered_tasks": sum(len(tasks) for tasks in registered_tasks.values()),
                "workers": list(active_tasks.keys()),
                "registry_stats": self.registry.get_stats(),
                "broker_url": self.broker_url,
                "result_backend": self.result_backend,
                "worker_stats": stats,
            }

        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {"active_tasks": 0, "registered_tasks": 0, "workers": [], "error": str(e)}

    def register_handler(self, handler: ITaskHandler) -> None:
        """注册Task processing器"""
        task_name = handler.task_name

        # 注册到内部注册表
        self.registry.register(task_name, handler)

        # 创建Celery任务装饰器
        @self.app.task(name=task_name, bind=True)
        def celery_task_wrapper(self_task, *args, **kwargs):
            """Celery任务包装器"""
            return asyncio.run(self._execute_handler(self_task, handler, *args, **kwargs))

        logger.info(f"Celery任务已注册: {task_name}")

    def unregister_handler(self, task_name: str) -> bool:
        """注销Task processing器"""
        # 从内部注册表注销
        success = self.registry.unregister(task_name)

        # TODO: 从Celery注销任务(Celery没有直接的注销方法)
        if success:
            logger.info(f"Task processing器已注销: {task_name}")

        return success

    def is_handler_registered(self, task_name: str) -> bool:
        """检查Task processing器是否已注册"""
        return self.registry.is_registered(task_name)

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {
            "service": self.service_name,
            "status": "healthy",
            "initialized": self._initialized,
            "broker_url": self.broker_url,
            "result_backend": self.result_backend,
        }

        try:
            # 检查Celery连接
            inspect = self.app.control.inspect()
            stats = inspect.stats()

            if stats:
                health["celery_workers"] = len(stats)
                health["worker_status"] = "connected"
            else:
                health["status"] = "degraded"
                health["worker_status"] = "no_workers"

        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)

        return health

    @property
    def service_name(self) -> str:
        """获取服务名称"""
        return f"CeleryTaskService[{self.app_name}]"

    async def _test_connection(self) -> None:
        """测试Celery连接"""
        try:
            # 尝试检查worker状态
            inspect = self.app.control.inspect()
            inspect.stats()  # 这会测试连接
        except Exception as e:
            raise TaskError(f"Celery连接测试失败: {e}")

    def _setup_task_routing(self) -> None:
        """设置任务路由"""
        # 根据任务名称和优先级设置路由规则
        self.app.conf.task_routes = {
            "rag.*": {"queue": "rag_queue"},
            "file.*": {"queue": "file_queue"},
            "notification.*": {"queue": "notification_queue"},
        }

        # 设置队列优先级
        self.app.conf.task_queue_max_priority = 10
        self.app.conf.worker_prefetch_multiplier = 1

    def _import_task_handlers(self) -> None:
        """导入Task processing器模块以触发装饰器注册"""
        try:
            # 导入所有Task processing器模块
            pass

            logger.info("Task processing器模块导入完成")
        except Exception as e:
            logger.warning(f"导入Task processing器模块失败: {e}")

    def _register_builtin_tasks(self) -> None:
        """注册内置任务"""

        # 注册健康检查任务
        @self.app.task(name="system.health_check")
        def health_check_task():
            return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

        logger.info("内置任务已注册")

    async def _execute_handler(self, celery_task, handler: ITaskHandler, *args, **kwargs) -> Any:
        """执行Task processing器"""
        task_id = celery_task.request.id

        try:
            logger.info(f"开始执行任务: {handler.task_name} (ID: {task_id})")

            # 执行Task processing器
            result = await handler.handle(*args, **kwargs)

            # 调用成功回调
            try:
                await handler.on_success(task_id, result)
            except Exception as e:
                logger.warning(f"Task success回调失败: {e}")

            logger.info(f"Task execution成功: {handler.task_name} (ID: {task_id})")
            return result

        except Exception as e:
            logger.error(f"Task execution失败: {handler.task_name} (ID: {task_id}), {e}")

            # 调用失败回调
            try:
                await handler.on_failure(task_id, e)
            except Exception as callback_error:
                logger.warning(f"Task failure回调失败: {callback_error}")

            # 检查是否需要重试
            config = handler.task_config
            if config.max_retries > 0 and celery_task.request.retries < config.max_retries:
                try:
                    await handler.on_retry(task_id, e, celery_task.request.retries)
                except Exception as retry_error:
                    logger.warning(f"Task retry回调失败: {retry_error}")

                # 抛出重试异常
                raise celery_task.retry(
                    exc=e, countdown=config.retry_delay, max_retries=config.max_retries
                )

            # 不重试，抛出原异常
            raise e

    def update_task_progress(self, task_id: str, progress: TaskProgress) -> None:
        """更新任务进度(供Task processing器调用)"""
        self._progress_store[task_id] = progress

        # 同时更新到Celery的状态存储
        try:
            self.app.backend.store_result(
                task_id,
                {
                    "progress": {
                        "current": progress.current,
                        "total": progress.total,
                        "description": progress.description,
                        "metadata": progress.metadata,
                    }
                },
                "PROGRESS",
            )
        except Exception as e:
            logger.debug(f"更新Celery进度失败: {e}")


# Task processing器装饰器
def task_handler(
    task_name: str,
    priority: TaskPriority = TaskPriority.NORMAL,
    max_retries: int = 3,
    retry_delay: int = 60,
    timeout: Optional[int] = None,
    queue: Optional[str] = None,
):
    """
    Task processing器装饰器

    Args:
        task_name: 任务名称
        priority: 任务优先级
        max_retries: 最大重试次数
        retry_delay: 重试延迟(秒)
        timeout: 超时时间(秒)
        queue: 指定队列
    """

    def decorator(handler_class: Type[ITaskHandler]):
        # 动态设置任务名称和配置
        original_task_name = handler_class.task_name
        original_task_config = handler_class.task_config

        # 重写属性
        handler_class.task_name = property(lambda self: task_name)
        handler_class.task_config = property(
            lambda self: TaskConfig(
                max_retries=max_retries,
                retry_delay=retry_delay,
                timeout=timeout,
                priority=priority,
                queue=queue,
            )
        )

        logger.info(f"Task processing器装饰器应用: {task_name}")
        return handler_class

    return decorator


# 全局任务注册表(用于自动发现)
_global_registry: Dict[str, Type[ITaskHandler]] = {}


def register_task_handler(handler_class: Type[ITaskHandler]) -> Type[ITaskHandler]:
    """注册Task processing器到全局注册表"""
    if hasattr(handler_class, "task_name"):
        task_name = (
            handler_class.task_name.fget(None)
            if isinstance(handler_class.task_name, property)
            else handler_class.task_name
        )
        _global_registry[task_name] = handler_class
        logger.info(f"Task processing器已注册到全局注册表: {task_name}")
    return handler_class


def get_global_handlers() -> Dict[str, Type[ITaskHandler]]:
    """获取所有全局注册的Task processing器"""
    return _global_registry.copy()


async def auto_register_handlers(task_service: ITaskService) -> int:
    """自动注册所有全局Task processing器"""
    count = 0
    for task_name, handler_class in _global_registry.items():
        try:
            handler_instance = handler_class()
            task_service.register_handler(handler_instance)
            count += 1
        except Exception as e:
            logger.error(f"自动注册Task processing器失败: {task_name}, {e}")

    logger.info(f"自动注册完成，共注册 {count} 个Task processing器")
    return count
