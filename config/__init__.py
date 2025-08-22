"""
系统配置模块

提供整个RAG知识管理系统的统一配置管理功能，包括：
- 应用程序配置
- 数据库配置
- 存储配置  
- 任务系统配置
- Redis配置
- 监控配置
等基础设施配置。
"""

# 统一配置系统 - 基于Pydantic BaseSettings
from .settings import (
    # 主要配置类
    AppConfig,
    Environment,
    get_config,
    reload_config,
    
    # 子配置类
    DatabaseConfig,
    StorageConfig,
    LoggingConfig,
    RedisConfig,
    WorkerConfig,
    TaskConfig,
    RetryConfig,
    MonitoringConfig,
    CeleryConfig
)

# 向后兼容的别名
PydanticAppConfig = AppConfig
PydanticDatabaseConfig = DatabaseConfig
PydanticStorageConfig = StorageConfig

# 默认配置实例
default_app_config = get_config()

# 存储相关的额外导入（如果需要）
try:
    from .storage import StorageProvider
except ImportError:
    # 如果storage.py文件不存在，从其他地方导入或定义默认值
    class StorageProvider:
        MINIO = "minio"
        AWS_S3 = "aws_s3"
        GOOGLE_GCS = "google_gcs"
        LOCAL = "local"

# API文档配置（从modules.config合并过来）
from .docs import (
    SWAGGER_UI_PARAMETERS,
    OPENAPI_TAGS,
    CUSTOM_SWAGGER_CSS,
    CUSTOM_SWAGGER_JS,
    get_openapi_config
)

# 任务监控配置（保留监控相关功能）
from .tasks.monitoring import (
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

__all__ = [
    # 主要配置类
    "AppConfig",
    "Environment", 
    "get_config",
    "reload_config",
    "default_app_config",
    
    # 子配置类
    "DatabaseConfig",
    "StorageConfig", 
    "StorageProvider",
    "LoggingConfig",
    "RedisConfig",
    "WorkerConfig",
    "TaskConfig",
    "RetryConfig",
    "MonitoringConfig",
    "CeleryConfig",
    
    # 向后兼容别名
    "PydanticAppConfig",
    "PydanticDatabaseConfig",
    "PydanticStorageConfig",
    
    # API文档配置
    "SWAGGER_UI_PARAMETERS",
    "OPENAPI_TAGS",
    "CUSTOM_SWAGGER_CSS",
    "CUSTOM_SWAGGER_JS",
    "get_openapi_config",
    
    # 任务监控接口
    "ITaskMonitoringService",
    "ITaskConfiguration",
    "ITaskAlerting",
    
    # 任务监控数据类
    "QueueMetrics",
    "TaskMetrics",
    "SystemHealth",
    "AlertRule",
    
    # 预定义常量
    "MONITORING_METRICS",
    "DEFAULT_ALERT_RULES"
]