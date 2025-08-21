"""
异步任务处理模块

为系统提供基于Celery的异步任务处理能力，支持：
- 任务提交和执行
- 任务状态跟踪
- 任务优先级和调度
- 错误处理和重试
- 任务处理器自动发现和注册
"""

from .base import (
    # 接口
    ITaskService,
    ITaskHandler,
    ITaskRegistry,
    
    # 枚举
    TaskStatus,
    TaskPriority,
    
    # 数据类
    TaskConfig,
    TaskResult,
    TaskProgress,
    
    # 异常
    TaskError,
    TaskTimeoutError,
    TaskRetryError,
    
    # 类型
    TaskHandlerDecorator
)

from config.tasks.monitoring import (
    # 监控接口
    ITaskMonitoringService,
    ITaskConfiguration,
    ITaskAlerting,
    
    # 监控数据类
    QueueMetrics,
    TaskMetrics,
    SystemHealth,
    AlertRule,
    
    # 预定义常量
    MONITORING_METRICS,
    DEFAULT_ALERT_RULES
)

from config.tasks.config import (
    # 配置数据类
    WorkerConfig,
    QueueConfig,
    TaskConfig as TaskConfigClass,
    RetryConfig,
    MonitoringConfig,
    RedisConfig,
    
    # 配置管理器
    TaskConfigManager,
    config_manager
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
    "QueueConfig",
    "TaskConfigClass",
    "RetryConfig",
    "MonitoringConfig",
    "RedisConfig",
    
    # 异常
    "TaskError",
    "TaskTimeoutError", 
    "TaskRetryError",
    
    # 类型
    "TaskHandlerDecorator",
    
    # 配置管理器
    "TaskConfigManager",
    "config_manager",
    
    # 预定义常量
    "MONITORING_METRICS",
    "DEFAULT_ALERT_RULES"
]