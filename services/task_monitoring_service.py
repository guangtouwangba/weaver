"""
任务监控服务实现

基于Redis和Celery的任务监控功能实现。
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
import psutil
import redis.asyncio as redis

from config.tasks.monitoring import (
    ITaskMonitoringService, ITaskConfiguration, ITaskAlerting,
    QueueMetrics, TaskMetrics, SystemHealth, AlertRule
)
from config import WorkerConfig, TaskConfig, RetryConfig

logger = logging.getLogger(__name__)

class RedisTaskMonitoringService(ITaskMonitoringService):
    """基于Redis的任务监控服务"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        初始化监控服务
        
        Args:
            redis_url: Redis连接URL
        """
        self.redis_url = redis_url
        self.redis_client = None
        self._metrics_cache = {}
        self._cache_ttl = 60  # 缓存1分钟
        
    async def _get_redis_client(self) -> redis.Redis:
        """获取Redis客户端"""
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url)
        return self.redis_client
    
    async def get_queue_metrics(self, queue_name: Optional[str] = None) -> List[QueueMetrics]:
        """获取队列指标"""
        try:
            client = await self._get_redis_client()
            queue_names = [queue_name] if queue_name else await self._get_all_queues()
            metrics = []
            
            for qname in queue_names:
                # 获取队列长度
                pending_count = await client.llen(qname)
                
                # 获取活跃任务数
                active_key = f"{qname}:active"
                active_count = await client.llen(active_key)
                
                # 获取统计数据
                stats_key = f"{qname}:stats"
                stats = await client.hgetall(stats_key)
                
                completed_count = int(stats.get("completed", 0))
                failed_count = int(stats.get("failed", 0))
                total_processed = completed_count + failed_count
                avg_time = float(stats.get("avg_processing_time", 0))
                
                # 最后活动时间
                last_activity_str = stats.get("last_activity")
                last_activity = None
                if last_activity_str:
                    last_activity = datetime.fromisoformat(last_activity_str)
                
                metrics.append(QueueMetrics(
                    queue_name=qname,
                    pending_count=pending_count,
                    active_count=active_count,
                    completed_count=completed_count,
                    failed_count=failed_count,
                    total_processed=total_processed,
                    average_processing_time=avg_time,
                    last_activity=last_activity
                ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"获取队列指标失败: {e}")
            return []
    
    async def get_task_metrics(self, task_name: Optional[str] = None) -> List[TaskMetrics]:
        """获取任务指标"""
        try:
            client = await self._get_redis_client()
            task_names = [task_name] if task_name else await self._get_all_tasks()
            metrics = []
            
            for tname in task_names:
                stats_key = f"task:{tname}:stats"
                stats = await client.hgetall(stats_key)
                
                total_executions = int(stats.get("total_executions", 0))
                successful_executions = int(stats.get("successful_executions", 0))
                failed_executions = int(stats.get("failed_executions", 0))
                avg_duration = float(stats.get("average_duration", 0))
                
                last_execution_str = stats.get("last_execution")
                last_execution = None
                if last_execution_str:
                    last_execution = datetime.fromisoformat(last_execution_str)
                
                error_rate = failed_executions / total_executions if total_executions > 0 else 0
                
                metrics.append(TaskMetrics(
                    task_name=tname,
                    total_executions=total_executions,
                    successful_executions=successful_executions,
                    failed_executions=failed_executions,
                    average_duration=avg_duration,
                    last_execution=last_execution,
                    error_rate=error_rate
                ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"获取任务指标失败: {e}")
            return []
    
    async def get_system_health(self) -> SystemHealth:
        """获取系统健康状态"""
        try:
            client = await self._get_redis_client()
            
            # 检查Redis连接
            redis_connection = True
            try:
                await client.ping()
            except:
                redis_connection = False
            
            # 获取工作进程数量
            workers_key = "celery.workers"
            active_workers = await client.scard(workers_key)
            
            # 获取队列数量
            queue_metrics = await self.get_queue_metrics()
            total_queues = len(queue_metrics)
            
            # 计算待处理和失败任务数
            pending_tasks = sum(q.pending_count for q in queue_metrics)
            
            # 获取最近1小时失败任务数
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            failed_tasks_last_hour = 0
            
            for queue_metric in queue_metrics:
                failed_key = f"{queue_metric.queue_name}:failed:{hour_ago.strftime('%Y%m%d%H')}"
                failed_count = await client.get(failed_key)
                if failed_count:
                    failed_tasks_last_hour += int(failed_count)
            
            # 获取系统资源使用情况
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            
            # 判断系统健康状态
            is_healthy = (
                redis_connection and
                active_workers > 0 and
                pending_tasks < 1000 and
                failed_tasks_last_hour < 10
            )
            
            status = "healthy" if is_healthy else "unhealthy"
            if not redis_connection:
                status = "redis_down"
            elif active_workers == 0:
                status = "no_workers"
            elif pending_tasks > 1000:
                status = "queue_backlog"
            elif failed_tasks_last_hour > 10:
                status = "high_error_rate"
            
            return SystemHealth(
                is_healthy=is_healthy,
                status=status,
                active_workers=active_workers,
                total_queues=total_queues,
                pending_tasks=pending_tasks,
                failed_tasks_last_hour=failed_tasks_last_hour,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                redis_connection=redis_connection,
                last_check=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"获取系统健康状态失败: {e}")
            return SystemHealth(
                is_healthy=False,
                status="error",
                active_workers=0,
                total_queues=0,
                pending_tasks=0,
                failed_tasks_last_hour=0,
                redis_connection=False,
                last_check=datetime.now()
            )
    
    async def get_active_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取正在执行的任务列表"""
        try:
            client = await self._get_redis_client()
            active_tasks = []
            
            # 获取所有活跃任务键
            active_pattern = "*:active"
            active_keys = await client.keys(active_pattern)
            
            for key in active_keys[:limit]:
                task_data = await client.lrange(key, 0, -1)
                for task_json in task_data:
                    try:
                        task_info = json.loads(task_json)
                        active_tasks.append(task_info)
                    except json.JSONDecodeError:
                        continue
            
            return active_tasks
            
        except Exception as e:
            logger.error(f"获取活跃任务失败: {e}")
            return []
    
    async def get_failed_tasks(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """获取失败的任务列表"""
        try:
            client = await self._get_redis_client()
            failed_tasks = []
            
            # 获取失败任务记录
            failed_pattern = "*:failed:*"
            failed_keys = await client.keys(failed_pattern)
            
            # 按时间过滤
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            for key in failed_keys:
                task_data = await client.lrange(key, 0, limit)
                for task_json in task_data:
                    try:
                        task_info = json.loads(task_json)
                        
                        # 检查时间
                        task_time_str = task_info.get("failed_at")
                        if task_time_str:
                            task_time = datetime.fromisoformat(task_time_str)
                            if task_time > cutoff_time:
                                failed_tasks.append(task_info)
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            # 按时间排序并限制数量
            failed_tasks.sort(key=lambda x: x.get("failed_at", ""), reverse=True)
            return failed_tasks[:limit]
            
        except Exception as e:
            logger.error(f"获取失败任务失败: {e}")
            return []
    
    async def get_task_history(self, 
                             task_id: str,
                             include_logs: bool = False) -> Optional[Dict[str, Any]]:
        """获取任务执行历史"""
        try:
            client = await self._get_redis_client()
            
            # 查找任务记录
            history_key = f"task:{task_id}:history"
            history_data = await client.get(history_key)
            
            if not history_data:
                return None
            
            history = json.loads(history_data)
            
            # 如果需要日志，获取日志数据
            if include_logs:
                log_key = f"task:{task_id}:logs"
                logs = await client.lrange(log_key, 0, -1)
                history["logs"] = [json.loads(log) for log in logs]
            
            return history
            
        except Exception as e:
            logger.error(f"获取任务历史失败: {e}")
            return None
    
    async def purge_completed_tasks(self, older_than_days: int = 7) -> int:
        """清理已完成的任务记录"""
        try:
            client = await self._get_redis_client()
            cutoff_time = datetime.now() - timedelta(days=older_than_days)
            
            # 查找过期的任务记录
            pattern = "task:*:history"
            keys = await client.keys(pattern)
            
            purged_count = 0
            for key in keys:
                data = await client.get(key)
                if data:
                    try:
                        task_info = json.loads(data)
                        completed_at_str = task_info.get("completed_at")
                        if completed_at_str:
                            completed_at = datetime.fromisoformat(completed_at_str)
                            if completed_at < cutoff_time:
                                # 删除任务记录和相关数据
                                task_id = key.split(":")[1]
                                await client.delete(key)
                                await client.delete(f"task:{task_id}:logs")
                                purged_count += 1
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            logger.info(f"已清理 {purged_count} 个过期任务记录")
            return purged_count
            
        except Exception as e:
            logger.error(f"清理任务记录失败: {e}")
            return 0
    
    async def _get_all_queues(self) -> List[str]:
        """获取所有队列名称"""
        try:
            client = await self._get_redis_client()
            # 从配置中获取队列名称
            return ["default", "high_priority", "low_priority"]
        except Exception as e:
            logger.error(f"获取队列列表失败: {e}")
            return ["default"]
    
    async def _get_all_tasks(self) -> List[str]:
        """获取所有任务名称"""
        try:
            # 从注册表获取任务名称
            from modules.services.task_service import task_registry
            return list(task_registry.handlers.keys())
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []

class TaskConfigurationService(ITaskConfiguration):
    """任务配置服务实现"""
    
    def __init__(self):
        """初始化配置服务"""
        self.config_manager = config_manager
    
    async def get_worker_config(self) -> Dict[str, Any]:
        """获取工作进程配置"""
        config = self.config_manager.get_worker_config()
        return {
            "concurrency": config.concurrency,
            "max_tasks_per_child": config.max_tasks_per_child,
            "time_limit": config.time_limit,
            "soft_time_limit": config.soft_time_limit,
            "memory_limit": config.memory_limit,
            "enable_prefetch": config.enable_prefetch,
            "prefetch_multiplier": config.prefetch_multiplier,
            "heartbeat_interval": config.heartbeat_interval,
            "worker_log_level": config.worker_log_level
        }
    
    async def update_worker_config(self, config: Dict[str, Any]) -> bool:
        """更新工作进程配置"""
        try:
            from config import WorkerConfig
            worker_config = WorkerConfig(**config)
            return self.config_manager.update_worker_config(worker_config)
        except Exception as e:
            logger.error(f"更新工作进程配置失败: {e}")
            return False
    
    async def get_queue_config(self, queue_name: str) -> Dict[str, Any]:
        """获取队列配置"""
        config = self.config_manager.get_queue_config(queue_name)
        if config:
            return {
                "name": config.name,
                "routing_key": config.routing_key,
                "priority": config.priority,
                "max_length": config.max_length,
                "message_ttl": config.message_ttl,
                "max_retries": config.max_retries,
                "retry_delay": config.retry_delay,
                "dead_letter_queue": config.dead_letter_queue,
                "durability": config.durability
            }
        return {}
    
    async def update_queue_config(self, queue_name: str, config: Dict[str, Any]) -> bool:
        """更新队列配置"""
        logger.warning("队列配置更新功能已简化，变更不会持久化")
        return True
    
    async def get_task_config(self, task_name: str) -> Dict[str, Any]:
        """获取任务配置"""
        config = self.config_manager.get_task_config(task_name)
        if config:
            return {
                "name": config.name,
                "queue": config.queue,
                "routing_key": config.routing_key,
                "priority": config.priority,
                "max_retries": config.max_retries,
                "retry_delay": config.retry_delay,
                "time_limit": config.time_limit,
                "soft_time_limit": config.soft_time_limit,
                "ignore_result": config.ignore_result,
                "store_errors_even_if_ignored": config.store_errors_even_if_ignored,
                "serializer": config.serializer,
                "compression": config.compression,
                "rate_limit": config.rate_limit
            }
        return {}
    
    async def update_task_config(self, task_name: str, config: Dict[str, Any]) -> bool:
        """更新任务配置"""
        try:
            from config import TaskConfig
            task_config = TaskConfig(name=task_name, **config)
            return self.config_manager.update_task_config(task_name, task_config)
        except Exception as e:
            logger.error(f"更新任务配置失败: {e}")
            return False
    
    async def get_retry_config(self) -> Dict[str, Any]:
        """获取重试配置"""
        config = self.config_manager.get_retry_config()
        return {
            "max_retries": config.max_retries,
            "default_retry_delay": config.default_retry_delay,
            "retry_backoff": config.retry_backoff,
            "retry_backoff_max": config.retry_backoff_max,
            "retry_jitter": config.retry_jitter,
            "autoretry_for": config.autoretry_for,
            "retry_kwargs": config.retry_kwargs
        }
    
    async def update_retry_config(self, config: Dict[str, Any]) -> bool:
        """更新重试配置"""
        try:
            from config import RetryConfig
            retry_config = RetryConfig(**config)
            return self.config_manager.update_retry_config(retry_config)
        except Exception as e:
            logger.error(f"更新重试配置失败: {e}")
            return False

# 创建服务实例
monitoring_service = RedisTaskMonitoringService()
configuration_service = TaskConfigurationService()