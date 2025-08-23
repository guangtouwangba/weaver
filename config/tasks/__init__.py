"""
任务系统配置模块

包含任务系统相关的所有配置管理功能。
"""

# 配置数据类已移动到 config.settings 中

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

__all__ = [
    # 监控接口
    "ITaskMonitoringService",
    "ITaskConfiguration",
    "ITaskAlerting",
    # 监控数据类
    "QueueMetrics",
    "TaskMetrics",
    "SystemHealth",
    "AlertRule",
    # 预定义常量
    "MONITORING_METRICS",
    "DEFAULT_ALERT_RULES",
]
