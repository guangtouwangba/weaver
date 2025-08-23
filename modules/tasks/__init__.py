"""
异步任务处理模块

为系统提供基于Celery的异步任务处理能力，支持：
- 任务提交和执行
- 任务状态跟踪
- 任务优先级和调度
- 错误处理和重试
- 任务处理器自动发现和注册
"""

from config import (
    CeleryConfig,
    MonitoringConfig,
    RedisConfig,
    RetryConfig,
)
from config import TaskConfig as TaskConfigClass  # 配置数据类
from config import (
    WorkerConfig,
)
from config.tasks.monitoring import (  # 监控接口; 监控数据类; 预定义常量
    DEFAULT_ALERT_RULES,
    MONITORING_METRICS,
    AlertRule,
    ITaskAlerting,
    ITaskConfiguration,
    ITaskMonitoringService,
    QueueMetrics,
    SystemHealth,
    TaskMetrics,
)
from modules.tasks.base import (  # 接口; 枚举; 数据类; 异常; 类型
    ITaskHandler,
    ITaskRegistry,
    ITaskService,
    TaskConfig,
    TaskError,
    TaskHandlerDecorator,
    TaskPriority,
    TaskProgress,
    TaskResult,
    TaskRetryError,
    TaskStatus,
    TaskTimeoutError,
)

__all__ = [
    # 核心接口
    "ITaskService",
    "ITaskHandler",
    "ITaskRegistry",
    # 监控接口
    "ITaskMonitoringService",
    "ITaskConfiguration",
    "ITaskAlerting",
    # 枚举
    "TaskStatus",
    "TaskPriority",
    # 数据类
    "TaskConfig",
    "TaskResult",
    "TaskProgress",
    # 监控数据类
    "QueueMetrics",
    "TaskMetrics",
    "SystemHealth",
    "AlertRule",
    # 配置数据类
    "WorkerConfig",
    "TaskConfigClass",
    "RetryConfig",
    "MonitoringConfig",
    "RedisConfig",
    "CeleryConfig",
    # 异常
    "TaskError",
    "TaskTimeoutError",
    "TaskRetryError",
    # 类型
    "TaskHandlerDecorator",
    # 预定义常量
    "MONITORING_METRICS",
    "DEFAULT_ALERT_RULES",
]
