"""
应用配置设置

使用pydantic管理配置，支持从环境变量和.env文件读取。
"""

import os
import getpass
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class RedisConfig(BaseModel):
    """Redis配置"""
    # 连接配置
    host: str = Field(default="localhost", description="Redis主机")
    port: int = Field(default=6379, description="Redis端口")
    db: int = Field(default=0, description="Redis数据库编号")
    password: Optional[str] = Field(default=None, description="Redis密码")
    username: Optional[str] = Field(default=None, description="Redis用户名")
    
    # 连接池配置
    max_connections: int = Field(default=50, description="最大连接数")
    
    # 超时配置
    socket_timeout: float = Field(default=5.0, description="socket超时时间")
    socket_connect_timeout: float = Field(default=5.0, description="socket连接超时时间")
    socket_keepalive: bool = Field(default=True, description="是否启用socket keepalive")
    
    # 重试配置
    retry_on_timeout: bool = Field(default=True, description="超时时是否重试")
    
    # SSL配置
    ssl: bool = Field(default=False, description="是否使用SSL")
    ssl_keyfile: Optional[str] = Field(default=None, description="SSL密钥文件")
    ssl_certfile: Optional[str] = Field(default=None, description="SSL证书文件")
    ssl_cert_reqs: str = Field(default="required", description="SSL证书要求")
    ssl_ca_certs: Optional[str] = Field(default=None, description="SSL CA证书")
    ssl_check_hostname: bool = Field(default=False, description="是否检查SSL主机名")
    
    # 缓存配置
    default_ttl: int = Field(default=3600, description="默认过期时间（秒）")
    key_prefix: str = Field(default="rag:", description="键前缀")
    serializer: str = Field(default="json", description="序列化器")
    compress: bool = Field(default=False, description="是否压缩数据")
    compress_threshold: int = Field(default=1024, description="压缩阈值（字节）")
    
    # 性能配置
    decode_responses: bool = Field(default=True, description="是否解码响应")
    encoding: str = Field(default="utf-8", description="编码")
    encoding_errors: str = Field(default="strict", description="编码错误处理")
    
    # 健康检查配置
    health_check_interval: int = Field(default=30, description="健康检查间隔")
    health_check_threshold: int = Field(default=50, description="健康检查阈值")

    @property
    def url(self) -> str:
        """构建Redis连接URL"""
        if self.password:
            if self.username:
                auth = f"{self.username}:{self.password}"
            else:
                auth = self.password
            url = f"redis://:{auth}@{self.host}:{self.port}/{self.db}"
        else:
            url = f"redis://{self.host}:{self.port}/{self.db}"
        
        if self.ssl:
            url = url.replace("redis://", "rediss://")
        
        return url


class WorkerConfig(BaseModel):
    """工作进程配置"""
    concurrency: int = Field(default=4, description="并发数")
    max_tasks_per_child: int = Field(default=1000, description="每个子进程最大任务数")
    time_limit: int = Field(default=3600, description="任务时间限制（秒）")
    soft_time_limit: int = Field(default=3000, description="任务软时间限制（秒）")
    memory_limit: int = Field(default=1024*1024*1024, description="内存限制（字节）")
    enable_prefetch: bool = Field(default=True, description="是否启用预取")
    prefetch_multiplier: int = Field(default=4, description="预取倍数")
    heartbeat_interval: int = Field(default=30, description="心跳间隔（秒）")
    worker_log_level: str = Field(default="INFO", description="工作进程日志级别")


class TaskConfig(BaseModel):
    """任务配置"""
    name: str = Field(description="任务名称")
    queue: str = Field(default="default", description="队列名称")
    routing_key: str = Field(default="", description="路由键")
    priority: int = Field(default=0, description="优先级")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: int = Field(default=60, description="重试延迟（秒）")
    time_limit: int = Field(default=300, description="时间限制（秒）")
    soft_time_limit: int = Field(default=240, description="软时间限制（秒）")
    ignore_result: bool = Field(default=False, description="是否忽略结果")
    store_errors_even_if_ignored: bool = Field(default=True, description="即使忽略也存储错误")
    serializer: str = Field(default="json", description="序列化器")
    compression: Optional[str] = Field(default=None, description="压缩方式")
    rate_limit: Optional[str] = Field(default=None, description="速率限制")


class RetryConfig(BaseModel):
    """重试配置"""
    max_retries: int = Field(default=3, description="最大重试次数")
    default_retry_delay: int = Field(default=60, description="默认重试延迟（秒）")
    retry_backoff: bool = Field(default=True, description="是否启用退避重试")
    retry_backoff_max: int = Field(default=600, description="最大退避时间（秒）")
    retry_jitter: bool = Field(default=True, description="是否启用重试抖动")
    autoretry_for: List[str] = Field(default_factory=list, description="自动重试的异常类型")


class MonitoringConfig(BaseModel):
    """监控配置"""
    enable_events: bool = Field(default=True, description="是否启用事件")
    enable_heartbeats: bool = Field(default=True, description="是否启用心跳")
    heartbeat_interval: int = Field(default=30, description="心跳间隔（秒）")
    events_queue: str = Field(default="celery.events", description="事件队列")
    monitor_frequency: int = Field(default=60, description="监控频率（秒）")
    metrics_retention_days: int = Field(default=30, description="指标保留天数")
    alert_email_enabled: bool = Field(default=False, description="是否启用邮件告警")
    alert_webhook_url: Optional[str] = Field(default=None, description="告警Webhook URL")


class CeleryConfig(BaseModel):
    """Celery配置"""
    broker_url: str = Field(default="redis://localhost:6379/0", description="消息代理URL")
    result_backend: str = Field(default="redis://localhost:6379/1", description="结果后端URL")
    app_name: str = Field(default="rag_tasks", description="应用名称")
    
    # 任务设置
    task_serializer: str = Field(default="json", description="任务序列化器")
    result_serializer: str = Field(default="json", description="结果序列化器")
    accept_content: List[str] = Field(default=["json"], description="接受的内容类型")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    enable_utc: bool = Field(default=True, description="是否启用UTC")
    result_expires: int = Field(default=3600, description="结果过期时间（秒）")
    
    # 工作进程设置
    worker_concurrency: int = Field(default=4, description="工作进程并发数")
    worker_max_tasks_per_child: int = Field(default=1000, description="每个子进程最大任务数")
    task_time_limit: int = Field(default=3600, description="任务时间限制（秒）")
    task_soft_time_limit: int = Field(default=3000, description="任务软时间限制（秒）")
    worker_prefetch_multiplier: int = Field(default=4, description="工作进程预取倍数")
    
    # 重试设置
    task_annotations: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "*": {
                "max_retries": 3,
                "default_retry_delay": 60
            }
        },
        description="任务注解"
    )
    
    # 监控设置
    worker_send_task_events: bool = Field(default=True, description="工作进程发送任务事件")
    task_send_sent_event: bool = Field(default=True, description="任务发送已发送事件")
    worker_heartbeat: int = Field(default=30, description="工作进程心跳间隔（秒）")
    
    # 队列路由
    task_routes: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="任务路由"
    )


class DatabaseConfig(BaseModel):
    """数据库配置"""
    
    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=5432, description="数据库端口") 
    name: str = Field(default="ragdb", description="数据库名称")
    user: str = Field(default_factory=getpass.getuser, description="数据库用户")
    password: Optional[str] = Field(default=None, description="数据库密码")
    driver: str = Field(default="asyncpg", description="数据库驱动")
    
    # 连接池配置
    pool_size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="最大溢出连接数")
    pool_timeout: int = Field(default=30, description="连接池超时时间")
    pool_recycle: int = Field(default=3600, description="连接回收时间")
    
    # 其他配置
    echo: bool = Field(default=False, description="是否显示SQL日志")
    
    @property
    def url(self) -> str:
        """构建数据库连接URL"""
        if self.password:
            return f"postgresql+{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            return f"postgresql+{self.driver}://{self.user}@{self.host}:{self.port}/{self.name}"
    
    @validator('driver')
    def validate_driver(cls, v):
        """验证数据库驱动"""
        allowed_drivers = ['asyncpg', 'psycopg2']
        if v not in allowed_drivers:
            raise ValueError(f"Driver must be one of {allowed_drivers}")
        return v


class StorageConfig(BaseModel):
    """存储配置"""
    
    provider: str = Field(default="local", description="存储提供商")
    bucket_name: str = Field(default="rag-files", description="存储桶名称")
    
    # 本地存储
    local_path: str = Field(default="./storage", description="本地存储路径")
    
    # MinIO配置
    minio_endpoint: str = Field(default="localhost:9000", description="MinIO端点")
    minio_access_key: str = Field(default="minioadmin", description="MinIO访问密钥")
    minio_secret_key: str = Field(default="minioadmin123", description="MinIO密钥")
    minio_secure: bool = Field(default=False, description="是否使用HTTPS")
    
    # AWS S3配置
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS访问密钥ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS密钥")
    aws_region: str = Field(default="us-east-1", description="AWS区域")
    
    @validator('provider')
    def validate_provider(cls, v):
        """验证存储提供商"""
        allowed_providers = ['local', 'minio', 's3', 'gcs', 'oss']
        if v not in allowed_providers:
            raise ValueError(f"Provider must be one of {allowed_providers}")
        return v


class LoggingConfig(BaseModel):
    """日志配置"""
    
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    file: Optional[str] = Field(default=None, description="日志文件路径")
    max_size: int = Field(default=10, description="日志文件最大大小(MB)")
    backup_count: int = Field(default=5, description="日志文件备份数量")


class AppConfig(BaseSettings):
    """应用程序主配置"""
    
    # 应用基础配置
    app_name: str = Field(default="RAG API", description="应用名称")
    app_version: str = Field(default="2.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    
    # 环境配置
    environment: str = Field(default="development", description="运行环境")
    
    # CORS配置
    cors_origins: Union[str, List[str]] = Field(default=["*"], description="允许的CORS源")
    cors_methods: Union[str, List[str]] = Field(default=["*"], description="允许的CORS方法")  
    cors_headers: Union[str, List[str]] = Field(default=["*"], description="允许的CORS头")
    
    # 子配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="数据库配置")
    storage: StorageConfig = Field(default_factory=StorageConfig, description="存储配置")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="日志配置")

    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis配置")
    
    celery: CeleryConfig = Field(default_factory=CeleryConfig, description="Celery配置")

    
    class Config:
        # 从.env文件读取环境变量
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"  # 支持嵌套配置，如 DATABASE__HOST
        case_sensitive = False
        
        # 环境变量前缀
        env_prefix = ""
        
        # 忽略未定义的额外字段，避免旧环境变量导致验证错误
        extra = "ignore"
    
    @validator('environment')
    def validate_environment(cls, v):
        """验证运行环境"""
        allowed_envs = ['development', 'testing', 'staging', 'production']
        if v.lower() not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v.lower()
    
    @validator('cors_origins', 'cors_methods', 'cors_headers')
    def validate_cors_list(cls, v):
        """验证CORS配置，支持字符串和列表格式"""
        if isinstance(v, str):
            # 如果是字符串，按逗号分割并去除空白
            if v.strip() == "*":
                return ["*"]
            return [item.strip() for item in v.split(',') if item.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["*"]
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == 'development'
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == 'production'


# 全局配置实例
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _config
    
    if _config is None:
        # 加载配置，自动从.env文件读取
        _config = AppConfig()
        
        # 如果存在自定义数据库URL环境变量，解析并覆盖配置
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            _config.database = _parse_database_url(database_url)
    
    return _config


def _parse_database_url(url: str) -> DatabaseConfig:
    """解析数据库URL为配置对象"""
    try:
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        
        # 解析驱动
        scheme_parts = parsed.scheme.split('+')
        if len(scheme_parts) == 2:
            driver = scheme_parts[1]
        else:
            driver = 'asyncpg'  # 默认驱动
        
        return DatabaseConfig(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 5432,
            name=parsed.path.lstrip('/') if parsed.path else 'ragdb',
            user=parsed.username or getpass.getuser(),
            password=parsed.password,
            driver=driver
        )
    except Exception as e:
        # 如果解析失败，返回默认配置
        import logging
        logging.warning(f"Failed to parse DATABASE_URL: {e}, using default config")
        return DatabaseConfig()


def reload_config() -> AppConfig:
    """重新加载配置"""
    global _config
    _config = None
    return get_config()
