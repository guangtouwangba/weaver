"""
日志上下文管理器

提供线程安全的日志上下文管理，支持结构化日志和分布式追踪。
"""

import asyncio
import threading
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime


# 用于异步上下文的ContextVar
_async_context: ContextVar[Optional['LogContext']] = ContextVar('log_context', default=None)

# 用于同步上下文的ThreadLocal
_sync_context = threading.local()


@dataclass
class LogContext:
    """日志上下文数据"""
    
    # 追踪信息
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # 业务上下文
    operation: Optional[str] = None
    component: Optional[str] = None
    service: Optional[str] = None
    
    # 性能信息
    started_at: Optional[datetime] = None
    
    # 自定义字段
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.utcnow()
        
        # 自动生成request_id
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        
        if self.request_id:
            result['request_id'] = self.request_id
        if self.correlation_id:
            result['correlation_id'] = self.correlation_id
        if self.session_id:
            result['session_id'] = self.session_id
        if self.user_id:
            result['user_id'] = self.user_id
        if self.operation:
            result['operation'] = self.operation
        if self.component:
            result['component'] = self.component
        if self.service:
            result['service'] = self.service
        
        if self.started_at:
            result['started_at'] = self.started_at.isoformat()
            result['duration'] = (datetime.utcnow() - self.started_at).total_seconds()
        
        # 添加自定义字段
        result.update(self.extra)
        
        return result
    
    def add_extra(self, key: str, value: Any):
        """添加额外字段"""
        self.extra[key] = value
    
    def remove_extra(self, key: str):
        """移除额外字段"""
        self.extra.pop(key, None)
    
    def copy(self) -> 'LogContext':
        """创建副本"""
        return LogContext(
            request_id=self.request_id,
            correlation_id=self.correlation_id,
            session_id=self.session_id,
            user_id=self.user_id,
            operation=self.operation,
            component=self.component,
            service=self.service,
            started_at=self.started_at,
            extra=self.extra.copy()
        )
    
    @classmethod
    def get_current(cls) -> Optional['LogContext']:
        """获取当前上下文"""
        # 优先尝试异步上下文
        try:
            async_ctx = _async_context.get()
            if async_ctx is not None:
                return async_ctx
        except LookupError:
            pass
        
        # 尝试同步上下文
        return getattr(_sync_context, 'context', None)
    
    @classmethod
    def set_current(cls, context: Optional['LogContext']):
        """设置当前上下文"""
        # 设置异步上下文
        try:
            _async_context.set(context)
        except LookupError:
            pass
        
        # 设置同步上下文
        _sync_context.context = context
    
    @classmethod
    def clear(cls):
        """清除当前上下文"""
        cls.set_current(None)


@contextmanager
def log_context(**kwargs) -> Generator[LogContext, None, None]:
    """
    日志上下文管理器
    
    Args:
        **kwargs: 上下文参数
        
    Yields:
        LogContext: 当前上下文对象
    """
    # 获取当前上下文
    current = LogContext.get_current()
    
    # 创建新上下文
    if current:
        # 继承现有上下文
        new_context = current.copy()
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(new_context, key):
                setattr(new_context, key, value)
            else:
                new_context.add_extra(key, value)
    else:
        # 创建新上下文
        new_context = LogContext(**kwargs)
    
    # 设置上下文
    LogContext.set_current(new_context)
    
    try:
        yield new_context
    finally:
        # 恢复原上下文
        LogContext.set_current(current)


@contextmanager
def request_context(request_id: str = None, 
                   user_id: str = None,
                   operation: str = None) -> Generator[LogContext, None, None]:
    """
    HTTP请求上下文管理器
    
    Args:
        request_id: 请求ID
        user_id: 用户ID
        operation: 操作名称
        
    Yields:
        LogContext: 请求上下文对象
    """
    with log_context(
        request_id=request_id or str(uuid.uuid4())[:8],
        user_id=user_id,
        operation=operation,
        component='http'
    ) as ctx:
        yield ctx


@contextmanager
def task_context(task_id: str,
                task_name: str,
                queue: str = None) -> Generator[LogContext, None, None]:
    """
    异步任务上下文管理器
    
    Args:
        task_id: 任务ID
        task_name: 任务名称
        queue: 队列名称
        
    Yields:
        LogContext: 任务上下文对象
    """
    with log_context(
        correlation_id=task_id,
        operation=task_name,
        component='task',
        queue=queue
    ) as ctx:
        yield ctx


class ContextLogger:
    """上下文感知的日志器包装器"""
    
    def __init__(self, logger):
        self._logger = logger
    
    def _log_with_context(self, level: int, msg: str, *args, **kwargs):
        """带上下文的日志记录"""
        # 获取当前上下文
        context = LogContext.get_current()
        
        if context:
            # 将上下文信息添加到extra中
            extra = kwargs.get('extra', {})
            extra.update(context.to_dict())
            kwargs['extra'] = extra
        
        # 记录日志
        self._logger.log(level, msg, *args, **kwargs)
    
    def debug(self, msg, *args, **kwargs):
        self._log_with_context(10, msg, *args, **kwargs)  # DEBUG = 10
    
    def info(self, msg, *args, **kwargs):
        self._log_with_context(20, msg, *args, **kwargs)  # INFO = 20
    
    def warning(self, msg, *args, **kwargs):
        self._log_with_context(30, msg, *args, **kwargs)  # WARNING = 30
    
    def error(self, msg, *args, **kwargs):
        self._log_with_context(40, msg, *args, **kwargs)  # ERROR = 40
    
    def critical(self, msg, *args, **kwargs):
        self._log_with_context(50, msg, *args, **kwargs)  # CRITICAL = 50
    
    def exception(self, msg, *args, **kwargs):
        """记录异常日志"""
        kwargs.setdefault('exc_info', True)
        self.error(msg, *args, **kwargs)
    
    # 转发其他方法到原始logger
    def __getattr__(self, name):
        return getattr(self._logger, name)


# 便捷函数
def get_request_id() -> Optional[str]:
    """获取当前请求ID"""
    context = LogContext.get_current()
    return context.request_id if context else None


def get_user_id() -> Optional[str]:
    """获取当前用户ID"""
    context = LogContext.get_current()
    return context.user_id if context else None


def set_user_id(user_id: str):
    """设置当前用户ID"""
    context = LogContext.get_current()
    if context:
        context.user_id = user_id
    else:
        LogContext.set_current(LogContext(user_id=user_id))


def add_context_field(key: str, value: Any):
    """添加上下文字段"""
    context = LogContext.get_current()
    if context:
        context.add_extra(key, value)
    else:
        LogContext.set_current(LogContext(extra={key: value}))


def remove_context_field(key: str):
    """移除上下文字段"""
    context = LogContext.get_current()
    if context:
        context.remove_extra(key)