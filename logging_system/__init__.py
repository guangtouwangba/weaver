"""
RAG系统专用日志系统

提供统一的日志配置、管理和使用接口，支持：
- 结构化日志输出
- 多种日志级别和处理器
- 上下文感知的日志记录
- 性能监控集成
- 异步日志支持
"""

from logging_system.config import (
    HandlerConfig,
    LogFormat,
    LoggingConfig,
    LogLevel,
    LogOutput,
)
from logging_system.context import (
    LogContext,
    log_context,
    request_context,
    task_context,
)
from logging_system.decorators import (
    log_errors,
    log_execution_time,
    log_method_calls,
    log_operation,
)
from logging_system.factory import LoggerFactory
from logging_system.formatters import (
    ColoredFormatter,
    JSONFormatter,
    RequestFormatter,
    StructuredFormatter,
)
from logging_system.handlers import (
    AsyncFileHandler,
    ElasticsearchHandler,
    RotatingFileHandler,
)

# AI Observability imports (optional)
try:
    from logging_system.ai_observability import (
        LogfireIntegration,
        get_logfire_integration,
        setup_logfire_integration,
        log_llm_call,
        log_rag_operation,
        log_document_processing,
        trace_span,
    )
    from logging_system.loki_handler import LokiHandler, AsyncLokiHandler
    AI_OBSERVABILITY_AVAILABLE = True
except ImportError:
    AI_OBSERVABILITY_AVAILABLE = False


# 便捷函数
def get_logger(name: str = None, **config):
    """
    获取配置好的日志器

    Args:
        name: 日志器名称，默认为调用模块名
        **config: 额外的配置参数

    Returns:
        Logger: 配置好的日志器实例
    """
    if name is None:
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "unknown")

    return LoggerFactory.get_logger(name, **config)


def setup_logging(config: LoggingConfig = None):
    """
    设置全局日志配置

    Args:
        config: 日志配置对象
    """
    if config is None:
        config = LoggingConfig()

    LoggerFactory.configure(config)


def configure_logging(config: LoggingConfig):
    """
    配置日志系统（别名）

    Args:
        config: 日志配置对象
    """
    LoggerFactory.configure(config)


# 默认初始化
_default_config = LoggingConfig()
LoggerFactory.configure(_default_config)

__all__ = [
    # 主要接口
    "get_logger",
    "setup_logging",
    "configure_logging",
    # 配置类
    "LoggingConfig",
    "LogLevel",
    "LogFormat",
    "LogOutput",
    "HandlerConfig",
    # 工厂类
    "LoggerFactory",
    # 格式化器
    "JSONFormatter",
    "StructuredFormatter",
    "ColoredFormatter",
    "RequestFormatter",
    # 处理器
    "AsyncFileHandler",
    "RotatingFileHandler",
    "ElasticsearchHandler",
    # 上下文和装饰器
    "LogContext",
    "log_context",
    "request_context",
    "task_context",
    "log_execution_time",
    "log_errors",
    "log_method_calls",
    "log_operation",
    # AI Observability (if available)
    "AI_OBSERVABILITY_AVAILABLE",
]

# Add AI observability exports if available
if AI_OBSERVABILITY_AVAILABLE:
    __all__.extend([
        "LogfireIntegration",
        "get_logfire_integration",
        "setup_logfire_integration",
        "log_llm_call",
        "log_rag_operation",
        "log_document_processing",
        "trace_span",
        "LokiHandler",
        "AsyncLokiHandler",
    ])
