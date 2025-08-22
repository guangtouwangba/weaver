"""
日志工厂模块

提供日志器的创建和配置管理，实现统一的日志系统接口。
"""

import logging
import sys
from typing import Dict, Optional, Any
from threading import Lock

from .config import LoggingConfig, LogLevel, LogFormat, LogOutput, HandlerConfig
from .formatters import create_formatter
from .handlers import create_handler
from .context import ContextLogger


class LoggerFactory:
    """日志器工厂类"""

    _instance = None
    _lock = Lock()
    _loggers: Dict[str, logging.Logger] = {}
    _config: Optional[LoggingConfig] = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def configure(cls, config: LoggingConfig):
        """配置日志系统"""
        with cls._lock:
            cls._config = config
            cls._setup_root_logger()

            # 重新配置已存在的日志器
            for name, logger in cls._loggers.items():
                cls._configure_logger(logger, name)

    @classmethod
    def get_logger(cls, name: str, **kwargs) -> ContextLogger:
        """
        获取日志器

        Args:
            name: 日志器名称
            **kwargs: 额外配置参数

        Returns:
            ContextLogger: 上下文感知的日志器
        """
        if cls._config is None:
            # 使用默认配置
            cls._config = LoggingConfig()
            cls._setup_root_logger()

        with cls._lock:
            if name not in cls._loggers:
                logger = logging.getLogger(name)
                cls._configure_logger(logger, name, **kwargs)
                cls._loggers[name] = logger

            return ContextLogger(cls._loggers[name])

    @classmethod
    def _setup_root_logger(cls):
        """设置根日志器"""
        if not cls._config:
            return

        root_logger = logging.getLogger()

        # 设置根级别
        root_level = getattr(logging, cls._config.level.value)
        root_logger.setLevel(root_level)

        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 添加配置的处理器
        for handler_config in cls._config.handlers:
            if handler_config.enabled:
                try:
                    handler = cls._create_handler(handler_config)
                    root_logger.addHandler(handler)
                except Exception as e:
                    sys.stderr.write(
                        f"Failed to create handler {handler_config.type}: {e}\n"
                    )

    @classmethod
    def _configure_logger(cls, logger: logging.Logger, name: str, **kwargs):
        """配置单个日志器"""
        if not cls._config:
            return

        # 设置日志级别
        module_level = cls._config.get_module_level(name)
        logger_level = getattr(logging, module_level.value)
        logger.setLevel(logger_level)

        # 检查是否需要排除
        if any(excluded in name for excluded in cls._config.exclude_modules):
            logger.disabled = True
            return

        # 设置传播
        logger.propagate = True

    @classmethod
    def _create_handler(cls, handler_config: HandlerConfig) -> logging.Handler:
        """创建日志处理器"""
        # 准备处理器参数
        handler_params = handler_config.extra_config.copy()

        # 根据处理器类型设置参数
        if handler_config.type == LogOutput.CONSOLE:
            pass  # StreamHandler不需要额外参数

        elif handler_config.type in [LogOutput.FILE, LogOutput.ASYNC_FILE]:
            if not handler_config.filename:
                raise ValueError(f"filename is required for {handler_config.type}")
            handler_params["filename"] = handler_config.filename

        elif handler_config.type == LogOutput.ROTATING_FILE:
            if not handler_config.filename:
                raise ValueError("filename is required for rotating file handler")
            handler_params.update(
                {
                    "filename": handler_config.filename,
                    "maxBytes": handler_config.max_bytes,
                    "backupCount": handler_config.backup_count,
                }
            )

        elif handler_config.type == LogOutput.ELASTICSEARCH:
            handler_params.update(
                {
                    "host": handler_config.es_host or "localhost",
                    "port": handler_config.es_port,
                    "index": handler_config.es_index or "logs",
                }
            )

        # 创建处理器
        handler = create_handler(handler_config.type.value, **handler_params)

        # 设置级别
        handler_level = getattr(logging, handler_config.level.value)
        handler.setLevel(handler_level)

        # 设置格式化器
        formatter = create_formatter(
            handler_config.format.value,
            include_context=cls._config.include_context,
            include_traceback=cls._config.include_traceback,
            sensitive_fields=cls._config.sensitive_fields,
        )
        handler.setFormatter(formatter)

        return handler

    @classmethod
    def get_config(cls) -> Optional[LoggingConfig]:
        """获取当前配置"""
        return cls._config

    @classmethod
    def set_level(cls, name: str, level: LogLevel):
        """设置特定日志器的级别"""
        if cls._config:
            cls._config.set_module_level(name, level)

            # 如果日志器已存在，立即应用新级别
            if name in cls._loggers:
                logger_level = getattr(logging, level.value)
                cls._loggers[name].setLevel(logger_level)

    @classmethod
    def add_handler_config(cls, handler_config: HandlerConfig):
        """添加处理器配置"""
        if cls._config:
            cls._config.add_handler(handler_config)

            # 为所有现有日志器添加新处理器
            try:
                handler = cls._create_handler(handler_config)
                logging.getLogger().addHandler(handler)
            except Exception as e:
                sys.stderr.write(f"Failed to add handler {handler_config.type}: {e}\n")

    @classmethod
    def remove_handler_type(cls, handler_type: LogOutput):
        """移除指定类型的处理器"""
        if cls._config:
            cls._config.remove_handler(handler_type)

            # 从根日志器移除相应处理器
            root_logger = logging.getLogger()
            handlers_to_remove = []

            for handler in root_logger.handlers:
                # 简单的类型判断
                handler_type_map = {
                    LogOutput.CONSOLE: logging.StreamHandler,
                    LogOutput.FILE: logging.FileHandler,
                    LogOutput.ROTATING_FILE: logging.handlers.RotatingFileHandler,
                }

                expected_type = handler_type_map.get(handler_type)
                if expected_type and isinstance(handler, expected_type):
                    handlers_to_remove.append(handler)

            for handler in handlers_to_remove:
                root_logger.removeHandler(handler)
                handler.close()

    @classmethod
    def get_logger_names(cls) -> list:
        """获取所有日志器名称"""
        return list(cls._loggers.keys())

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """获取日志系统统计信息"""
        stats = {
            "total_loggers": len(cls._loggers),
            "logger_names": list(cls._loggers.keys()),
            "config_loaded": cls._config is not None,
        }

        if cls._config:
            stats.update(
                {
                    "global_level": cls._config.level.value,
                    "handlers_count": len(cls._config.handlers),
                    "enabled_handlers": [
                        h.type.value for h in cls._config.handlers if h.enabled
                    ],
                    "module_specific_levels": {
                        name: level.value
                        for name, level in cls._config.module_levels.items()
                    },
                }
            )

        return stats

    @classmethod
    def reset(cls):
        """重置日志系统"""
        with cls._lock:
            # 关闭所有处理器
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
                handler.close()

            # 清理缓存
            cls._loggers.clear()
            cls._config = None

    @classmethod
    def health_check(cls) -> Dict[str, Any]:
        """健康检查"""
        health = {
            "status": "healthy",
            "config_loaded": cls._config is not None,
            "loggers_count": len(cls._loggers),
            "handlers_status": {},
        }

        if cls._config:
            # 检查各个处理器
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                handler_name = handler.__class__.__name__
                try:
                    # 尝试写入测试日志
                    test_record = logging.LogRecord(
                        name="test",
                        level=logging.INFO,
                        pathname="",
                        lineno=0,
                        msg="health check",
                        args=(),
                        exc_info=None,
                    )
                    handler.handle(test_record)
                    health["handlers_status"][handler_name] = "healthy"
                except Exception as e:
                    health["handlers_status"][handler_name] = f"error: {e}"
                    health["status"] = "degraded"

        return health


# 便捷别名
factory = LoggerFactory()
