"""
任务配置管理模块

提供任务系统的配置管理功能，包括工作进程配置、队列配置、重试策略等。
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import yaml

logger = logging.getLogger(__name__)

@dataclass
class WorkerConfig:
    """工作进程配置"""
    concurrency: int = 4
    max_tasks_per_child: int = 1000
    time_limit: int = 3600  # 1小时
    soft_time_limit: int = 3000  # 50分钟
    memory_limit: int = 1024 * 1024 * 1024  # 1GB
    enable_prefetch: bool = True
    prefetch_multiplier: int = 4
    heartbeat_interval: int = 30
    worker_log_level: str = "INFO"

@dataclass
class QueueConfig:
    """队列配置"""
    name: str
    routing_key: str
    priority: int = 0
    max_length: Optional[int] = None
    message_ttl: Optional[int] = None  # 消息存活时间（秒）
    max_retries: int = 3
    retry_delay: int = 60  # 重试延迟（秒）
    dead_letter_queue: Optional[str] = None
    durability: bool = True  # 队列持久化

@dataclass
class TaskConfig:
    """任务配置"""
    name: str
    queue: str = "default"
    routing_key: str = ""
    priority: int = 0
    max_retries: int = 3
    retry_delay: int = 60
    time_limit: int = 300  # 5分钟
    soft_time_limit: int = 240  # 4分钟
    ignore_result: bool = False
    store_errors_even_if_ignored: bool = True
    serializer: str = "json"
    compression: Optional[str] = None
    rate_limit: Optional[str] = None  # 例如: "100/m" (每分钟100次)

@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    default_retry_delay: int = 60
    retry_backoff: bool = True
    retry_backoff_max: int = 600
    retry_jitter: bool = True
    autoretry_for: list = None  # 自动重试的异常类型
    retry_kwargs: Dict[str, Any] = None

@dataclass
class RedisConfig:
    """Redis配置"""
    # 连接配置
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    username: Optional[str] = None
    
    # 连接池配置
    max_connections: int = 50
    connection_pool_class_kwargs: Dict[str, Any] = None
    
    # 超时配置
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    socket_keepalive: bool = True
    socket_keepalive_options: Dict[str, Any] = None
    
    # 重试配置
    retry_on_timeout: bool = True
    retry_on_error: List[str] = None  # 重试的错误类型
    
    # SSL配置
    ssl: bool = False
    ssl_keyfile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_cert_reqs: str = "required"
    ssl_ca_certs: Optional[str] = None
    ssl_check_hostname: bool = False
    
    # 集群配置
    cluster_enabled: bool = False
    cluster_nodes: List[Dict[str, Any]] = None
    cluster_require_full_coverage: bool = True
    cluster_skip_full_coverage_check: bool = False
    
    # 哨兵配置
    sentinel_enabled: bool = False
    sentinel_hosts: List[Dict[str, Any]] = None
    sentinel_master_name: str = "mymaster"
    sentinel_socket_timeout: float = 0.1
    
    # 缓存配置
    default_ttl: int = 3600  # 默认过期时间（秒）
    key_prefix: str = "rag:"  # 键前缀
    serializer: str = "json"  # json, pickle, msgpack
    compress: bool = False  # 是否压缩数据
    compress_threshold: int = 1024  # 压缩阈值（字节）
    
    # 性能配置
    decode_responses: bool = True
    encoding: str = "utf-8"
    encoding_errors: str = "strict"
    
    # 健康检查配置
    health_check_interval: int = 30
    health_check_threshold: int = 50

@dataclass
class MonitoringConfig:
    """监控配置"""
    enable_events: bool = True
    enable_heartbeats: bool = True
    heartbeat_interval: int = 30
    events_queue: str = "celery.events"
    monitor_frequency: int = 60  # 监控频率（秒）
    metrics_retention_days: int = 30
    alert_email_enabled: bool = False
    alert_webhook_url: Optional[str] = None

class TaskConfigManager:
    """任务配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，支持JSON和YAML格式
        """
        self.config_file = config_file
        self._config_cache = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not self.config_file or not Path(self.config_file).exists():
            logger.info("使用默认配置")
            self._config_cache = self._get_default_config()
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            self._config_cache = config
            logger.info(f"已加载配置文件: {self.config_file}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config_cache = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "worker": asdict(WorkerConfig()),
            "queues": {
                "default": asdict(QueueConfig(name="default", routing_key="default")),
                "high_priority": asdict(QueueConfig(
                    name="high_priority", 
                    routing_key="high_priority",
                    priority=10
                )),
                "low_priority": asdict(QueueConfig(
                    name="low_priority", 
                    routing_key="low_priority",
                    priority=1
                ))
            },
            "tasks": {},
            "retry": asdict(RetryConfig()),
            "monitoring": asdict(MonitoringConfig()),
            "redis": asdict(RedisConfig())
        }
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        if not self.config_file:
            logger.warning("未指定配置文件路径，无法保存")
            return False
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(self._config_cache, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
                else:
                    json.dump(self._config_cache, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到: {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get_worker_config(self) -> WorkerConfig:
        """获取工作进程配置"""
        config_dict = self._config_cache.get("worker", {})
        return WorkerConfig(**config_dict)
    
    def update_worker_config(self, config: WorkerConfig) -> bool:
        """更新工作进程配置"""
        try:
            self._config_cache["worker"] = asdict(config)
            return self.save_config()
        except Exception as e:
            logger.error(f"更新工作进程配置失败: {e}")
            return False
    
    def get_queue_config(self, queue_name: str) -> Optional[QueueConfig]:
        """获取队列配置"""
        queues = self._config_cache.get("queues", {})
        queue_dict = queues.get(queue_name)
        if queue_dict:
            return QueueConfig(**queue_dict)
        return None
    
    def update_queue_config(self, queue_name: str, config: QueueConfig) -> bool:
        """更新队列配置"""
        try:
            if "queues" not in self._config_cache:
                self._config_cache["queues"] = {}
            
            self._config_cache["queues"][queue_name] = asdict(config)
            return self.save_config()
        except Exception as e:
            logger.error(f"更新队列配置失败: {e}")
            return False
    
    def get_task_config(self, task_name: str) -> Optional[TaskConfig]:
        """获取任务配置"""
        tasks = self._config_cache.get("tasks", {})
        task_dict = tasks.get(task_name)
        if task_dict:
            return TaskConfig(**task_dict)
        return None
    
    def update_task_config(self, task_name: str, config: TaskConfig) -> bool:
        """更新任务配置"""
        try:
            if "tasks" not in self._config_cache:
                self._config_cache["tasks"] = {}
            
            self._config_cache["tasks"][task_name] = asdict(config)
            return self.save_config()
        except Exception as e:
            logger.error(f"更新任务配置失败: {e}")
            return False
    
    def get_retry_config(self) -> RetryConfig:
        """获取重试配置"""
        config_dict = self._config_cache.get("retry", {})
        return RetryConfig(**config_dict)
    
    def update_retry_config(self, config: RetryConfig) -> bool:
        """更新重试配置"""
        try:
            self._config_cache["retry"] = asdict(config)
            return self.save_config()
        except Exception as e:
            logger.error(f"更新重试配置失败: {e}")
            return False
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """获取监控配置"""
        config_dict = self._config_cache.get("monitoring", {})
        return MonitoringConfig(**config_dict)
    
    def update_monitoring_config(self, config: MonitoringConfig) -> bool:
        """更新监控配置"""
        try:
            self._config_cache["monitoring"] = asdict(config)
            return self.save_config()
        except Exception as e:
            logger.error(f"更新监控配置失败: {e}")
            return False
    
    def get_redis_config(self) -> RedisConfig:
        """获取Redis配置"""
        config_dict = self._config_cache.get("redis", {})
        return RedisConfig(**config_dict)
    
    def update_redis_config(self, config: RedisConfig) -> bool:
        """更新Redis配置"""
        try:
            self._config_cache["redis"] = asdict(config)
            return self.save_config()
        except Exception as e:
            logger.error(f"更新Redis配置失败: {e}")
            return False
    
    def list_queues(self) -> List[str]:
        """列出所有队列名称"""
        return list(self._config_cache.get("queues", {}).keys())
    
    def list_tasks(self) -> List[str]:
        """列出所有任务名称"""
        return list(self._config_cache.get("tasks", {}).keys())
    
    def reload_config(self) -> bool:
        """重新加载配置文件"""
        try:
            self._load_config()
            logger.info("配置已重新加载")
            return True
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            return False
    
    def get_celery_config(self) -> Dict[str, Any]:
        """生成Celery配置字典"""
        worker_config = self.get_worker_config()
        retry_config = self.get_retry_config()
        monitoring_config = self.get_monitoring_config()
        redis_config = self.get_redis_config()
        
        # 构建Redis URL
        broker_url = self._build_redis_url(redis_config, db=0)
        result_backend = self._build_redis_url(redis_config, db=1)
        
        return {
            # 基础设置
            "broker_url": broker_url,
            "result_backend": result_backend,
            
            # Redis连接配置
            "redis_socket_timeout": redis_config.socket_timeout,
            "redis_socket_connect_timeout": redis_config.socket_connect_timeout,
            "redis_socket_keepalive": redis_config.socket_keepalive,
            "redis_retry_on_timeout": redis_config.retry_on_timeout,
            "redis_max_connections": redis_config.max_connections,
            
            # 工作进程设置
            "worker_concurrency": worker_config.concurrency,
            "worker_max_tasks_per_child": worker_config.max_tasks_per_child,
            "task_time_limit": worker_config.time_limit,
            "task_soft_time_limit": worker_config.soft_time_limit,
            "worker_prefetch_multiplier": worker_config.prefetch_multiplier,
            
            # 任务设置
            "task_serializer": redis_config.serializer,
            "result_serializer": redis_config.serializer,
            "accept_content": [redis_config.serializer, "json"],
            "timezone": "Asia/Shanghai",
            "enable_utc": True,
            "result_expires": redis_config.default_ttl,
            
            # 重试设置
            "task_annotations": {
                "*": {
                    "max_retries": retry_config.max_retries,
                    "default_retry_delay": retry_config.default_retry_delay
                }
            },
            
            # 监控设置
            "worker_send_task_events": monitoring_config.enable_events,
            "task_send_sent_event": monitoring_config.enable_events,
            "worker_heartbeat": monitoring_config.heartbeat_interval,
            
            # 队列路由
            "task_routes": self._build_task_routes()
        }
    
    def _build_task_routes(self) -> Dict[str, Dict[str, str]]:
        """构建任务路由配置"""
        routes = {}
        tasks = self._config_cache.get("tasks", {})
        
        for task_name, task_config in tasks.items():
            routes[task_name] = {
                "queue": task_config.get("queue", "default"),
                "routing_key": task_config.get("routing_key", "default")
            }
        
        return routes
    
    def _build_redis_url(self, redis_config: RedisConfig, db: Optional[int] = None) -> str:
        """构建Redis连接URL"""
        # 使用指定的db或配置中的db
        database = db if db is not None else redis_config.db
        
        # 构建基础URL
        if redis_config.password:
            if redis_config.username:
                auth = f"{redis_config.username}:{redis_config.password}"
            else:
                auth = redis_config.password
            url = f"redis://:{auth}@{redis_config.host}:{redis_config.port}/{database}"
        else:
            url = f"redis://{redis_config.host}:{redis_config.port}/{database}"
        
        # 添加SSL支持
        if redis_config.ssl:
            url = url.replace("redis://", "rediss://")
        
        return url
    
    def get_redis_connection_params(self) -> Dict[str, Any]:
        """获取Redis连接参数字典"""
        redis_config = self.get_redis_config()
        
        params = {
            "host": redis_config.host,
            "port": redis_config.port,
            "db": redis_config.db,
            "decode_responses": redis_config.decode_responses,
            "encoding": redis_config.encoding,
            "encoding_errors": redis_config.encoding_errors,
            "socket_timeout": redis_config.socket_timeout,
            "socket_connect_timeout": redis_config.socket_connect_timeout,
            "socket_keepalive": redis_config.socket_keepalive,
            "retry_on_timeout": redis_config.retry_on_timeout,
            "max_connections": redis_config.max_connections,
            "health_check_interval": redis_config.health_check_interval,
        }
        
        # 添加认证信息
        if redis_config.password:
            params["password"] = redis_config.password
        if redis_config.username:
            params["username"] = redis_config.username
        
        # 添加SSL配置
        if redis_config.ssl:
            params["ssl"] = True
            if redis_config.ssl_keyfile:
                params["ssl_keyfile"] = redis_config.ssl_keyfile
            if redis_config.ssl_certfile:
                params["ssl_certfile"] = redis_config.ssl_certfile
            if redis_config.ssl_ca_certs:
                params["ssl_ca_certs"] = redis_config.ssl_ca_certs
            params["ssl_cert_reqs"] = redis_config.ssl_cert_reqs
            params["ssl_check_hostname"] = redis_config.ssl_check_hostname
        
        # 添加连接池配置
        if redis_config.connection_pool_class_kwargs:
            params.update(redis_config.connection_pool_class_kwargs)
        
        # 添加keepalive选项
        if redis_config.socket_keepalive_options:
            params["socket_keepalive_options"] = redis_config.socket_keepalive_options
        
        return params
    
    def build_redis_cluster_config(self) -> Optional[Dict[str, Any]]:
        """构建Redis集群配置"""
        redis_config = self.get_redis_config()
        
        if not redis_config.cluster_enabled or not redis_config.cluster_nodes:
            return None
        
        return {
            "startup_nodes": redis_config.cluster_nodes,
            "decode_responses": redis_config.decode_responses,
            "skip_full_coverage_check": redis_config.cluster_skip_full_coverage_check,
            "require_full_coverage": redis_config.cluster_require_full_coverage,
            "socket_timeout": redis_config.socket_timeout,
            "socket_connect_timeout": redis_config.socket_connect_timeout,
            "retry_on_timeout": redis_config.retry_on_timeout,
            "password": redis_config.password,
            "username": redis_config.username,
        }
    
    def build_redis_sentinel_config(self) -> Optional[Dict[str, Any]]:
        """构建Redis哨兵配置"""
        redis_config = self.get_redis_config()
        
        if not redis_config.sentinel_enabled or not redis_config.sentinel_hosts:
            return None
        
        return {
            "sentinels": redis_config.sentinel_hosts,
            "service_name": redis_config.sentinel_master_name,
            "socket_timeout": redis_config.sentinel_socket_timeout,
            "password": redis_config.password,
            "username": redis_config.username,
            "db": redis_config.db,
            "decode_responses": redis_config.decode_responses,
        }

# 全局配置管理器实例
config_manager = TaskConfigManager()