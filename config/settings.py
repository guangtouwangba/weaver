"""
应用配置设置

使用pydantic管理配置，支持从环境变量和.env文件读取。
"""

import os
import getpass
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class Environment(Enum):
    """环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


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


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    
    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=5432, description="数据库端口") 
    name: str = Field(default="ragdb", description="数据库名称")
    user: str = Field(default="rag_user", description="数据库用户")
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
        from urllib.parse import quote_plus
        if self.password:
            # URL编码密码以处理特殊字符
            encoded_password = quote_plus(self.password)
            return f"postgresql+{self.driver}://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.name}"
        else:
            return f"postgresql+{self.driver}://{self.user}@{self.host}:{self.port}/{self.name}"
    
    @validator('driver')
    def validate_driver(cls, v):
        """验证数据库驱动"""
        allowed_drivers = ['asyncpg', 'psycopg2']
        if v not in allowed_drivers:
            raise ValueError(f"Driver must be one of {allowed_drivers}")
        return v
    
    @validator('password')
    def validate_password(cls, v, values):
        """验证密码安全性"""
        import os
        environment = os.getenv('ENVIRONMENT', 'development')
        
        # 生产环境必须设置密码
        if environment == 'production' and not v:
            raise ValueError("生产环境必须设置数据库密码")
        
        # 密码强度检查（如果设置了密码）
        if v:
            if len(v) < 8:
                raise ValueError("密码长度不能少于8位")
            
            # 检查密码复杂度（至少包含字母和数字）
            has_letter = any(c.isalpha() for c in v)
            has_digit = any(c.isdigit() for c in v)
            
            if not (has_letter and has_digit):
                import warnings
                warnings.warn("建议密码包含字母和数字，提高安全性", UserWarning)
        
        return v
    
    class Config:
        env_prefix = "DATABASE__"
        case_sensitive = False
    
    @validator('user')
    def validate_user(cls, v):
        """验证用户名"""
        if not v or v.strip() == "":
            # 如果用户名为空，使用系统用户名作为后备
            import getpass
            return getpass.getuser()
        return v.strip()
    
    def validate_security(self) -> List[str]:
        """检查配置安全性，返回警告列表"""
        warnings = []
        import os
        environment = os.getenv('ENVIRONMENT', 'development')
        
        if not self.password:
            if environment == 'production':
                warnings.append("生产环境未设置数据库密码，存在安全风险")
            else:
                warnings.append("未设置数据库密码，建议设置以提高安全性")
        
        if self.host == "localhost" and environment == 'production':
            warnings.append("生产环境使用localhost可能导致连接问题")
        
        if self.user in ['postgres', 'root', 'admin'] and environment == 'production':
            warnings.append("生产环境建议使用专用数据库用户，而非管理员账户")
        
        return warnings


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


class OpenAIConfig(BaseModel):
    """OpenAI Configuration"""
    api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    api_base: Optional[str] = Field(default=None, description="OpenAI API Base URL")
    organization: Optional[str] = Field(default=None, description="OpenAI Organization ID")
    
    # Model configurations
    chat_model: str = Field(default="gpt-3.5-turbo", description="Default chat model")
    embedding_model: str = Field(default="text-embedding-ada-002", description="Default embedding model")
    
    # Request configurations
    max_tokens: int = Field(default=1024, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="Generation temperature")
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class AnthropicConfig(BaseModel):
    """Anthropic Configuration"""
    api_key: Optional[str] = Field(default=None, description="Anthropic API Key")
    api_base: Optional[str] = Field(default=None, description="Anthropic API Base URL")
    
    # Model configurations
    chat_model: str = Field(default="claude-3-sonnet-20240229", description="Default chat model")
    
    # Request configurations
    max_tokens: int = Field(default=1024, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="Generation temperature")
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class HuggingFaceConfig(BaseModel):
    """HuggingFace Configuration"""
    api_key: Optional[str] = Field(default=None, description="HuggingFace API Key")
    api_base: Optional[str] = Field(default="https://api-inference.huggingface.co", description="HuggingFace API Base URL")
    
    # Model configurations
    chat_model: str = Field(default="microsoft/DialoGPT-medium", description="Default chat model")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Default embedding model")
    
    # Request configurations
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class LocalLLMConfig(BaseModel):
    """Local LLM Configuration (Ollama, etc.)"""
    api_base: str = Field(default="http://localhost:11434", description="Local LLM API Base URL")
    
    # Model configurations
    chat_model: str = Field(default="llama2", description="Default chat model")
    embedding_model: str = Field(default="nomic-embed-text", description="Default embedding model")
    
    # Request configurations
    timeout: int = Field(default=120, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class EmbeddingConfig(BaseModel):
    """Embedding Service Configuration"""
    provider: str = Field(default="openai", description="Embedding provider (openai, huggingface, local)")
    
    # Provider-specific configurations
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    huggingface: HuggingFaceConfig = Field(default_factory=HuggingFaceConfig)
    local: LocalLLMConfig = Field(default_factory=LocalLLMConfig)
    
    # General embedding settings
    chunk_size: int = Field(default=1000, description="Text chunk size for embeddings")
    overlap: int = Field(default=200, description="Chunk overlap size")
    batch_size: int = Field(default=100, description="Batch size for embedding requests")

    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ["openai", "huggingface", "local"]
        if v not in allowed_providers:
            raise ValueError(f"Embedding provider must be one of {allowed_providers}")
        return v


class ChatConfig(BaseModel):
    """Chat Service Configuration"""
    provider: str = Field(default="openai", description="Chat provider (openai, anthropic, huggingface, local)")
    
    # Provider-specific configurations
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    huggingface: HuggingFaceConfig = Field(default_factory=HuggingFaceConfig)
    local: LocalLLMConfig = Field(default_factory=LocalLLMConfig)
    
    # General chat settings
    max_context_length: int = Field(default=4000, description="Maximum context length")
    system_prompt: str = Field(default="You are a helpful AI assistant.", description="Default system prompt")

    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ["openai", "anthropic", "huggingface", "local"]
        if v not in allowed_providers:
            raise ValueError(f"Chat provider must be one of {allowed_providers}")
        return v


class AIConfig(BaseModel):
    """AI Services Configuration"""
    # Provider configurations
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig, description="Embedding service configuration")
    chat: ChatConfig = Field(default_factory=ChatConfig, description="Chat service configuration")
    
    # Global AI settings
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    enable_fallback: bool = Field(default=True, description="Enable provider fallback")
    
    # Rate limiting
    rate_limit_requests_per_minute: int = Field(default=60, description="Rate limit per minute")
    rate_limit_tokens_per_minute: int = Field(default=100000, description="Token rate limit per minute")


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
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="运行环境")
    
    # API配置
    api_prefix: str = Field(default="/api/v1", description="API前缀")
    docs_url: Optional[str] = Field(default="/docs", description="文档URL")
    redoc_url: Optional[str] = Field(default="/redoc", description="ReDoc URL")
    openapi_url: Optional[str] = Field(default="/openapi.json", description="OpenAPI JSON URL")
    
    # 安全配置
    secret_key: str = Field(default="your-secret-key-here", description="应用密钥")
    allowed_hosts: List[str] = Field(default=["*"], description="允许的主机")
    
    # CORS配置
    cors_origins: Union[str, List[str]] = Field(default=["*"], description="允许的CORS源")
    cors_methods: Union[str, List[str]] = Field(default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], description="允许的CORS方法")  
    cors_headers: Union[str, List[str]] = Field(default=["*"], description="允许的CORS头")
    cors_credentials: bool = Field(default=True, description="是否允许凭据")
    
    # 性能配置
    request_timeout: int = Field(default=30, description="请求超时时间")
    keepalive_timeout: int = Field(default=5, description="保持连接超时时间")
    max_request_size: int = Field(default=100 * 1024 * 1024, description="最大请求大小")
    
    # 文件处理配置
    max_file_size: int = Field(default=100 * 1024 * 1024, description="最大文件大小")
    allowed_file_types: List[str] = Field(
        default=[
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/markdown",
            "text/html",
            "text/csv",
            "application/json"
        ],
        description="允许的文件类型"
    )
    upload_timeout: int = Field(default=300, description="上传超时时间")
    
    # RAG配置
    default_chunk_size: int = Field(default=1000, description="默认分块大小")
    chunk_overlap: int = Field(default=200, description="分块重叠")
    max_chunks_per_document: int = Field(default=1000, description="每个文档最大分块数")
    
    # 监控配置
    enable_metrics: bool = Field(default=True, description="是否启用指标")
    metrics_path: str = Field(default="/metrics", description="指标路径")
    health_check_path: str = Field(default="/health", description="健康检查路径")
    
    # 子配置
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="数据库配置")
    storage: StorageConfig = Field(default_factory=StorageConfig, description="存储配置")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="日志配置")
    ai: AIConfig = Field(default_factory=AIConfig, description="AI服务配置")

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
    
    @validator('environment', pre=True)
    def validate_environment(cls, v):
        """验证运行环境"""
        if isinstance(v, str):
            try:
                return Environment(v.lower())
            except ValueError:
                allowed_envs = [e.value for e in Environment]
                raise ValueError(f"Environment must be one of {allowed_envs}")
        return v
    
    def model_post_init(self, __context):
        """配置初始化后处理 - 根据环境调整配置"""
        # 生产环境安全调整
        if self.environment == Environment.PRODUCTION:
            self.debug = False
            self.docs_url = None
            self.redoc_url = None 
            self.openapi_url = None
            if self.allowed_hosts == ["*"]:
                self.allowed_hosts = []
            if self.cors_origins == ["*"]:
                self.cors_origins = []
        
        # 开发环境便利性调整
        elif self.environment == Environment.DEVELOPMENT:
            self.debug = True
    
    def get_cors_config(self) -> Dict[str, Any]:
        """获取CORS配置"""
        origins = self.cors_origins if isinstance(self.cors_origins, list) else [self.cors_origins]
        methods = self.cors_methods if isinstance(self.cors_methods, list) else [self.cors_methods]
        headers = self.cors_headers if isinstance(self.cors_headers, list) else [self.cors_headers]
        
        return {
            "allow_origins": origins,
            "allow_credentials": self.cors_credentials,
            "allow_methods": methods,
            "allow_headers": headers
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        log_level = self.logging.level.upper()
        log_file = self.logging.file
        
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "json": {
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": log_level
                }
            },
            "root": {
                "level": log_level,
                "handlers": ["console"]
            }
        }
        
        # 添加文件日志处理器
        if log_file:
            config["handlers"]["file"] = {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": log_file,
                "when": "D",
                "interval": 1,
                "backupCount": 30,
                "formatter": "json" if self.environment == Environment.PRODUCTION else "default",
                "level": log_level
            }
            config["root"]["handlers"].append("file")
        
        return config
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == Environment.DEVELOPMENT
    
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
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """从环境变量创建配置实例 - 便捷方法"""
        return cls()


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
