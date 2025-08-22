"""
RAG系统专用日志系统

提供统一的日志配置、管理和使用接口，支持：
- 结构化日志输出
- 多种日志级别和处理器
- 上下文感知的日志记录
- 性能监控集成
- 异步日志支持
"""

from .factory import LoggerFactory
from .config import LoggingConfig, LogLevel, LogFormat, LogOutput, HandlerConfig
from .formatters import (
    JSONFormatter,
    StructuredFormatter,
    ColoredFormatter,
    RequestFormatter,
)
from .handlers import AsyncFileHandler, RotatingFileHandler, ElasticsearchHandler
from .context import LogContext, log_context, request_context, task_context
from .decorators import log_execution_time, log_errors, log_method_calls, log_operation


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
]
