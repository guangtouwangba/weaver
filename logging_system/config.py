"""
日志系统配置模块

定义日志配置类和相关枚举，支持灵活的日志配置管理。
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class LogLevel(Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(Enum):
    """日志格式枚举"""

    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"
    COLORED = "colored"
    STRUCTURED = "structured"


class LogOutput(Enum):
    """日志输出目标"""

    CONSOLE = "console"
    FILE = "file"
    ROTATING_FILE = "rotating_file"
    ELASTICSEARCH = "elasticsearch"
    ASYNC_FILE = "async_file"
    LOKI = "loki"
    ASYNC_LOKI = "async_loki"
    BOTH = "both"  # Console + File


@dataclass
class HandlerConfig:
    """日志处理器配置"""

    type: LogOutput
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.DETAILED
    enabled: bool = True

    # 文件相关配置
    filename: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

    # Elasticsearch相关配置
    es_host: Optional[str] = None
    es_port: int = 9200
    es_index: Optional[str] = None

    # Loki相关配置
    loki_url: Optional[str] = None
    loki_labels: Optional[Dict[str, str]] = None

    # 其他配置
    extra_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoggingConfig:
    """完整的日志系统配置"""

    # 基本配置
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.DETAILED
    output: LogOutput = LogOutput.CONSOLE

    # 应用信息
    app_name: str = "rag-system"
    version: str = "1.0.0"
    environment: str = "development"

    # 日志目录和文件配置
    log_dir: str = "logs"
    file_path: Optional[str] = None
    
    # 文件轮转配置
    enable_file_rotation: bool = True
    max_file_size: int = 10  # MB
    backup_count: int = 5

    # 处理器配置
    handlers: List[HandlerConfig] = field(
        default_factory=lambda: [
            HandlerConfig(
                type=LogOutput.CONSOLE, level=LogLevel.INFO, format=LogFormat.COLORED
            ),
            HandlerConfig(
                type=LogOutput.ROTATING_FILE,
                level=LogLevel.DEBUG,
                format=LogFormat.DETAILED,
                filename="app.log",
            ),
        ]
    )

    # 特定模块的日志级别
    module_levels: Dict[str, LogLevel] = field(default_factory=dict)

    # 上下文配置
    include_context: bool = True
    include_traceback: bool = True
    include_performance: bool = False

    # 异步配置
    async_logging: bool = False
    async_queue_size: int = 1000

    # 过滤器配置
    exclude_modules: List[str] = field(default_factory=list)
    sensitive_fields: List[str] = field(
        default_factory=lambda: ["password", "token", "api_key", "secret", "credential"]
    )

    def __post_init__(self):
        """初始化后处理"""
        # 确保日志目录存在
        if self.log_dir:
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)

        # 如果指定了 file_path，且 output 为 BOTH，自动配置handlers
        if self.output == LogOutput.BOTH and self.file_path:
            self.handlers = [
                HandlerConfig(
                    type=LogOutput.CONSOLE,
                    level=self.level,
                    format=LogFormat.COLORED
                ),
                HandlerConfig(
                    type=LogOutput.ROTATING_FILE if self.enable_file_rotation else LogOutput.FILE,
                    level=self.level,
                    format=LogFormat.DETAILED,
                    filename=self.file_path,
                    max_bytes=self.max_file_size * 1024 * 1024,
                    backup_count=self.backup_count
                )
            ]

        # 为每个handler设置默认文件名
        for handler in self.handlers:
            if handler.type in [
                LogOutput.FILE,
                LogOutput.ROTATING_FILE,
                LogOutput.ASYNC_FILE,
            ]:
                if not handler.filename:
                    handler.filename = f"{self.app_name}.log"

                # 如果是相对路径，加上日志目录
                if not os.path.isabs(handler.filename):
                    handler.filename = os.path.join(self.log_dir, handler.filename)

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """从环境变量创建配置"""
        config = cls()

        # 从环境变量读取基本配置
        if level := os.getenv("LOG_LEVEL"):
            try:
                config.level = LogLevel(level.upper())
            except ValueError:
                pass

        if format_type := os.getenv("LOG_FORMAT"):
            try:
                config.format = LogFormat(format_type.lower())
            except ValueError:
                pass

        config.app_name = os.getenv("APP_NAME", config.app_name)
        config.version = os.getenv("APP_VERSION", config.version)
        config.environment = os.getenv("ENVIRONMENT", config.environment)
        config.log_dir = os.getenv("LOG_DIR", config.log_dir)

        # 异步配置
        if async_log := os.getenv("ASYNC_LOGGING"):
            config.async_logging = async_log.lower() in ("true", "1", "yes")

        # 上下文配置
        if include_context := os.getenv("LOG_INCLUDE_CONTEXT"):
            config.include_context = include_context.lower() in ("true", "1", "yes")

        if include_perf := os.getenv("LOG_INCLUDE_PERFORMANCE"):
            config.include_performance = include_perf.lower() in ("true", "1", "yes")

        return config

    @classmethod
    def for_development(cls) -> "LoggingConfig":
        """开发环境配置"""
        return cls(
            level=LogLevel.DEBUG,
            format=LogFormat.COLORED,
            environment="development",
            include_context=True,
            include_performance=True,
            handlers=[
                HandlerConfig(
                    type=LogOutput.CONSOLE,
                    level=LogLevel.DEBUG,
                    format=LogFormat.COLORED,
                ),
                HandlerConfig(
                    type=LogOutput.ROTATING_FILE,
                    level=LogLevel.DEBUG,
                    format=LogFormat.DETAILED,
                    filename="debug.log",
                    max_bytes=5 * 1024 * 1024,  # 5MB
                    backup_count=3,
                ),
            ],
        )

    @classmethod
    def for_production(cls) -> "LoggingConfig":
        """生产环境配置"""
        return cls(
            level=LogLevel.INFO,
            format=LogFormat.JSON,
            environment="production",
            include_context=False,
            include_performance=False,
            async_logging=True,
            handlers=[
                HandlerConfig(
                    type=LogOutput.CONSOLE,
                    level=LogLevel.WARNING,
                    format=LogFormat.JSON,
                ),
                HandlerConfig(
                    type=LogOutput.ASYNC_FILE,
                    level=LogLevel.INFO,
                    format=LogFormat.JSON,
                    filename="app.log",
                    max_bytes=50 * 1024 * 1024,  # 50MB
                    backup_count=10,
                ),
                HandlerConfig(
                    type=LogOutput.ASYNC_FILE,
                    level=LogLevel.ERROR,
                    format=LogFormat.JSON,
                    filename="error.log",
                    max_bytes=20 * 1024 * 1024,  # 20MB
                    backup_count=5,
                ),
                # Loki for centralized log aggregation
                HandlerConfig(
                    type=LogOutput.ASYNC_LOKI,
                    level=LogLevel.INFO,
                    format=LogFormat.JSON,
                    loki_url="http://loki:3100",
                    loki_labels={"environment": "production", "service": "rag-system"},
                ),
            ],
        )

    @classmethod 
    def for_observability(cls) -> "LoggingConfig":
        """AI观测性增强配置"""
        return cls(
            level=LogLevel.DEBUG,
            format=LogFormat.JSON,
            environment="development",
            include_context=True,
            include_performance=True,
            async_logging=True,
            handlers=[
                HandlerConfig(
                    type=LogOutput.CONSOLE,
                    level=LogLevel.INFO,
                    format=LogFormat.COLORED,
                ),
                HandlerConfig(
                    type=LogOutput.ASYNC_LOKI,
                    level=LogLevel.DEBUG,
                    format=LogFormat.JSON,
                    loki_url="http://localhost:3100",
                    loki_labels={"environment": "development", "service": "rag-system"},
                ),
                HandlerConfig(
                    type=LogOutput.ROTATING_FILE,
                    level=LogLevel.DEBUG,
                    format=LogFormat.JSON,
                    filename="observability.log",
                    max_bytes=10 * 1024 * 1024,  # 10MB
                    backup_count=3,
                ),
            ],
        )

    @classmethod
    def for_testing(cls) -> "LoggingConfig":
        """测试环境配置"""
        return cls(
            level=LogLevel.WARNING,
            format=LogFormat.SIMPLE,
            environment="testing",
            include_context=False,
            include_performance=False,
            handlers=[
                HandlerConfig(
                    type=LogOutput.CONSOLE,
                    level=LogLevel.WARNING,
                    format=LogFormat.SIMPLE,
                )
            ],
        )

    def get_handler_config(self, handler_type: LogOutput) -> Optional[HandlerConfig]:
        """获取指定类型的处理器配置"""
        for handler in self.handlers:
            if handler.type == handler_type and handler.enabled:
                return handler
        return None

    def add_handler(self, handler_config: HandlerConfig):
        """添加处理器配置"""
        self.handlers.append(handler_config)

    def remove_handler(self, handler_type: LogOutput):
        """移除指定类型的处理器"""
        self.handlers = [h for h in self.handlers if h.type != handler_type]

    def set_module_level(self, module_name: str, level: LogLevel):
        """设置特定模块的日志级别"""
        self.module_levels[module_name] = level

    def get_module_level(self, module_name: str) -> LogLevel:
        """获取模块的日志级别"""
        # 尝试精确匹配
        if module_name in self.module_levels:
            return self.module_levels[module_name]

        # 尝试父模块匹配
        parts = module_name.split(".")
        for i in range(len(parts) - 1, 0, -1):
            parent = ".".join(parts[:i])
            if parent in self.module_levels:
                return self.module_levels[parent]

        # 返回默认级别
        return self.level
