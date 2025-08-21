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

# 应用程序配置
from .app import (
    AppConfig,
    Environment,
    default_app_config
)

# 数据库配置
from .database import (
    DatabaseConfig,
    default_db_config
)

# 存储配置
from .storage import (
    StorageConfig,
    StorageProvider,
    default_storage_config
)

# 应用程序设置配置（从modules.config合并过来）
from .settings import (
    AppConfig as PydanticAppConfig,
    DatabaseConfig as PydanticDatabaseConfig,
    StorageConfig as PydanticStorageConfig,
    LoggingConfig,
    get_config,
    reload_config
)

# API文档配置（从modules.config合并过来）
from .docs import (
    SWAGGER_UI_PARAMETERS,
    OPENAPI_TAGS,
    CUSTOM_SWAGGER_CSS,
    CUSTOM_SWAGGER_JS,
    get_openapi_config
)

# 任务系统配置
from .tasks.config import (
    # 配置数据类
    WorkerConfig,
    QueueConfig,
    TaskConfig,
    RetryConfig,
    MonitoringConfig,
    RedisConfig,
    
    # 配置管理器
    TaskConfigManager,
    config_manager
)

# 任务监控配置
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
    # 应用程序配置
    "AppConfig",
    "Environment", 
    "default_app_config",
    
    # 数据库配置
    "DatabaseConfig",
    "default_db_config",
    
    # 存储配置
    "StorageConfig",
    "StorageProvider",
    "default_storage_config",
    
    # Pydantic应用程序设置配置（从modules.config合并过来）
    "PydanticAppConfig",
    "PydanticDatabaseConfig",
    "PydanticStorageConfig",
    "LoggingConfig",
    "get_config",
    "reload_config",
    
    # API文档配置（从modules.config合并过来）
    "SWAGGER_UI_PARAMETERS",
    "OPENAPI_TAGS",
    "CUSTOM_SWAGGER_CSS",
    "CUSTOM_SWAGGER_JS",
    "get_openapi_config",
    
    # 任务配置数据类
    "WorkerConfig",
    "QueueConfig", 
    "TaskConfig",
    "RetryConfig",
    "MonitoringConfig",
    "RedisConfig",
    
    # 任务配置管理器
    "TaskConfigManager",
    "config_manager",
    
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