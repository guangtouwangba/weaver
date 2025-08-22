"""
Log context manager

Provides thread-safe log context management supporting structured logging and distributed tracing.
"""

import asyncio
import threading
import uuid
from contextlib import contextmanager
from typing import Dict, Any, Optional, Generator
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime


# ContextVar for async context
_async_context: ContextVar[Optional['LogContext']] = ContextVar('log_context', default=None)

# ThreadLocal for sync context
_sync_context = threading.local()


@dataclass
class LogContext:
    """Log context data"""
    
    # Tracing information
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Business context
    operation: Optional[str] = None
    component: Optional[str] = None
    service: Optional[str] = None
    
    # Performance information
    started_at: Optional[datetime] = None
    
    # Custom fields
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.utcnow()
        
        # Auto-generate request_id
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
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
        
        # Add custom fields
        result.update(self.extra)
        
        return result
    
    def add_extra(self, key: str, value: Any):
        """Add extra field"""
        self.extra[key] = value
    
    def remove_extra(self, key: str):
        """Remove extra field"""
        self.extra.pop(key, None)
    
    def copy(self) -> 'LogContext':
        """Create copy"""
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
        """Get current context"""
        # Try async context first
        try:
            async_ctx = _async_context.get()
            if async_ctx is not None:
                return async_ctx
        except LookupError:
            pass
        
        # Try sync context
        return getattr(_sync_context, 'context', None)
    
    @classmethod
    def set_current(cls, context: Optional['LogContext']):
        """Set current context"""
        # Set async context
        try:
            _async_context.set(context)
        except LookupError:
            pass
        
        # Set sync context
        _sync_context.context = context
    
    @classmethod
    def clear(cls):
        """Clear current context"""
        cls.set_current(None)


@contextmanager
def log_context(**kwargs) -> Generator[LogContext, None, None]:
    """
    Log context manager
    
    Args:
        **kwargs: Context parameters
        
    Yields:
        LogContext: Current context object
    """
    # Get current context
    current = LogContext.get_current()
    
    # Create new context
    if current:
        # Inherit existing context
        new_context = current.copy()
        # Update fields
        for key, value in kwargs.items():
            if hasattr(new_context, key):
                setattr(new_context, key, value)
            else:
                new_context.add_extra(key, value)
    else:
        # Create new context
        new_context = LogContext(**kwargs)
    
    # Set context
    LogContext.set_current(new_context)
    
    try:
        yield new_context
    finally:
        # Restore original context
        LogContext.set_current(current)


@contextmanager
def request_context(request_id: str = None, 
                   user_id: str = None,
                   operation: str = None) -> Generator[LogContext, None, None]:
    """
    HTTP request context manager
    
    Args:
        request_id: Request ID
        user_id: User ID
        operation: Operation name
        
    Yields:
        LogContext: Request context object
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
    Async task context manager
    
    Args:
        task_id: Task ID
        task_name: Task name
        queue: Queue name
        
    Yields:
        LogContext: Task context object
    """
    with log_context(
        correlation_id=task_id,
        operation=task_name,
        component='task',
        queue=queue
    ) as ctx:
        yield ctx


class ContextLogger:
    """Context-aware logger wrapper"""
    
    def __init__(self, logger):
        self._logger = logger
    
    def _log_with_context(self, level: int, msg: str, *args, **kwargs):
        """Log with context"""
        # Get current context
        context = LogContext.get_current()
        
        if context:
            # Add context info to extra
            extra = kwargs.get('extra', {})
            extra.update(context.to_dict())
            kwargs['extra'] = extra
        
        # Log record
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
        """Log exception"""
        kwargs.setdefault('exc_info', True)
        self.error(msg, *args, **kwargs)
    
    # Forward other methods to original logger
    def __getattr__(self, name):
        return getattr(self._logger, name)


# Convenience functions
def get_request_id() -> Optional[str]:
    """Get current request ID"""
    context = LogContext.get_current()
    return context.request_id if context else None


def get_user_id() -> Optional[str]:
    """Get current user ID"""
    context = LogContext.get_current()
    return context.user_id if context else None


def set_user_id(user_id: str):
    """Set current user ID"""
    context = LogContext.get_current()
    if context:
        context.user_id = user_id
    else:
        LogContext.set_current(LogContext(user_id=user_id))


def add_context_field(key: str, value: Any):
    """Add context field"""
    context = LogContext.get_current()
    if context:
        context.add_extra(key, value)
    else:
        LogContext.set_current(LogContext(extra={key: value}))


def remove_context_field(key: str):
    """Remove context field"""
    context = LogContext.get_current()
    if context:
        context.remove_extra(key)