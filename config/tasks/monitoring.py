"""
任务监控模块

提供任务系统的监控功能，包括队列状态、任务指标统计和健康检查。
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum

# 定义任务状态和优先级枚举（避免循环导入）
class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    SUCCESS = "success"      # 执行成功
    FAILURE = "failure"      # 执行失败
    RETRY = "retry"          # 重试中
    REVOKED = "revoked"      # 已取消

class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1          # 低优先级
    NORMAL = 5       # 普通优先级
    HIGH = 8         # 高优先级
    CRITICAL = 10    # 关键优先级

logger = logging.getLogger(__name__)

@dataclass
class QueueMetrics:
    """队列指标数据"""
    queue_name: str
    pending_count: int
    active_count: int
    completed_count: int
    failed_count: int
    total_processed: int
    average_processing_time: float
    last_activity: Optional[datetime] = None

@dataclass
class TaskMetrics:
    """任务指标数据"""
    task_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_duration: float
    last_execution: Optional[datetime] = None
    error_rate: float = 0.0

@dataclass
class SystemHealth:
    """系统健康状态"""
    is_healthy: bool
    status: str
    active_workers: int
    total_queues: int
    pending_tasks: int
    failed_tasks_last_hour: int
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    redis_connection: bool = True
    last_check: datetime = None

class ITaskMonitoringService(ABC):
    """任务监控服务接口"""
    
    @abstractmethod
    async def get_queue_metrics(self, queue_name: Optional[str] = None) -> List[QueueMetrics]:
        """获取队列指标"""
        pass
    
    @abstractmethod
    async def get_task_metrics(self, task_name: Optional[str] = None) -> List[TaskMetrics]:
        """获取任务指标"""
        pass
    
    @abstractmethod
    async def get_system_health(self) -> SystemHealth:
        """获取系统健康状态"""
        pass
    
    @abstractmethod
    async def get_active_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取正在执行的任务列表"""
        pass
    
    @abstractmethod
    async def get_failed_tasks(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """获取失败的任务列表"""
        pass
    
    @abstractmethod
    async def get_task_history(self, 
                             task_id: str,
                             include_logs: bool = False) -> Optional[Dict[str, Any]]:
        """获取任务执行历史"""
        pass
    
    @abstractmethod
    async def purge_completed_tasks(self, older_than_days: int = 7) -> int:
        """清理已完成的任务记录"""
        pass

class ITaskConfiguration(ABC):
    """任务配置接口"""
    
    @abstractmethod
    async def get_worker_config(self) -> Dict[str, Any]:
        """获取工作进程配置"""
        pass
    
    @abstractmethod
    async def update_worker_config(self, config: Dict[str, Any]) -> bool:
        """更新工作进程配置"""
        pass
    
    @abstractmethod
    async def get_queue_config(self, queue_name: str) -> Dict[str, Any]:
        """获取队列配置"""
        pass
    
    @abstractmethod
    async def update_queue_config(self, queue_name: str, config: Dict[str, Any]) -> bool:
        """更新队列配置"""
        pass
    
    @abstractmethod
    async def get_task_config(self, task_name: str) -> Dict[str, Any]:
        """获取任务配置"""
        pass
    
    @abstractmethod
    async def update_task_config(self, task_name: str, config: Dict[str, Any]) -> bool:
        """更新任务配置"""
        pass
    
    @abstractmethod
    async def get_retry_config(self) -> Dict[str, Any]:
        """获取重试配置"""
        pass
    
    @abstractmethod
    async def update_retry_config(self, config: Dict[str, Any]) -> bool:
        """更新重试配置"""
        pass

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    condition: str  # 告警条件表达式
    threshold: float
    severity: str  # 'critical', 'warning', 'info'
    enabled: bool = True
    description: str = ""

class ITaskAlerting(ABC):
    """任务告警接口"""
    
    @abstractmethod
    async def create_alert_rule(self, rule: AlertRule) -> bool:
        """创建告警规则"""
        pass
    
    @abstractmethod
    async def update_alert_rule(self, rule_name: str, rule: AlertRule) -> bool:
        """更新告警规则"""
        pass
    
    @abstractmethod
    async def delete_alert_rule(self, rule_name: str) -> bool:
        """删除告警规则"""
        pass
    
    @abstractmethod
    async def list_alert_rules(self) -> List[AlertRule]:
        """列出所有告警规则"""
        pass
    
    @abstractmethod
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """检查并触发告警"""
        pass
    
    @abstractmethod
    async def send_alert(self, 
                        alert_type: str,
                        message: str,
                        severity: str = "warning") -> bool:
        """发送告警通知"""
        pass

# 预定义的监控指标
MONITORING_METRICS = {
    "queue_length": "队列长度",
    "processing_rate": "处理速率",
    "error_rate": "错误率",
    "average_processing_time": "平均处理时间",
    "worker_utilization": "工作进程利用率",
    "memory_usage": "内存使用率",
    "failed_tasks_rate": "任务失败率"
}

# 预定义的告警规则模板
DEFAULT_ALERT_RULES = [
    AlertRule(
        name="high_error_rate",
        condition="error_rate > threshold",
        threshold=0.1,  # 10%
        severity="critical",
        description="任务错误率过高"
    ),
    AlertRule(
        name="queue_backlog",
        condition="queue_length > threshold",
        threshold=1000,
        severity="warning",
        description="队列积压过多"
    ),
    AlertRule(
        name="worker_down",
        condition="active_workers < threshold",
        threshold=1,
        severity="critical",
        description="工作进程不足"
    ),
    AlertRule(
        name="slow_processing",
        condition="average_processing_time > threshold",
        threshold=300,  # 5分钟
        severity="warning",
        description="任务处理速度过慢"
    )
]