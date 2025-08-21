"""
日志装饰器模块

提供常用的日志装饰器，用于自动记录函数执行、错误和性能信息。
"""

import asyncio
import functools
import inspect
import time
from typing import Any, Callable, Optional, Dict, Union
from contextlib import contextmanager

from .factory import LoggerFactory
from .config import LogLevel
from .context import log_context


def log_execution_time(
    logger_name: str = None,
    level: LogLevel = LogLevel.INFO,
    include_args: bool = False,
    include_result: bool = False,
    threshold_ms: Optional[float] = None
):
    """
    记录函数执行时间的装饰器
    
    Args:
        logger_name: 日志器名称，默认使用函数所在模块
        level: 日志级别
        include_args: 是否包含参数信息
        include_result: 是否包含返回结果
        threshold_ms: 只记录超过此阈值的执行时间（毫秒）
    """
    def decorator(func: Callable) -> Callable:
        # 获取日志器
        nonlocal logger_name
        if logger_name is None:
            logger_name = func.__module__
        
        logger = LoggerFactory.get_logger(logger_name)
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                
                try:
                    with log_context(operation=func.__name__, component='async_function'):
                        result = await func(*args, **kwargs)
                        execution_time = (time.perf_counter() - start_time) * 1000
                        
                        # 检查阈值
                        if threshold_ms is None or execution_time >= threshold_ms:
                            log_message = f"Function {func.__name__} executed in {execution_time:.2f}ms"
                            
                            extra_data = {'execution_time_ms': execution_time}
                            
                            if include_args:
                                extra_data['function_args'] = args
                                extra_data['function_kwargs'] = kwargs
                            
                            if include_result:
                                extra_data['result'] = result
                            
                            getattr(logger, level.value.lower())(log_message, extra=extra_data)
                        
                        return result
                        
                except Exception as e:
                    execution_time = (time.perf_counter() - start_time) * 1000
                    logger.error(
                        f"Function {func.__name__} failed after {execution_time:.2f}ms",
                        extra={
                            'execution_time_ms': execution_time,
                            'error': str(e),
                            'error_type': type(e).__name__
                        },
                        exc_info=True
                    )
                    raise
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                
                try:
                    with log_context(operation=func.__name__, component='function'):
                        result = func(*args, **kwargs)
                        execution_time = (time.perf_counter() - start_time) * 1000
                        
                        # 检查阈值
                        if threshold_ms is None or execution_time >= threshold_ms:
                            log_message = f"Function {func.__name__} executed in {execution_time:.2f}ms"
                            
                            extra_data = {'execution_time_ms': execution_time}
                            
                            if include_args:
                                extra_data['function_args'] = args
                                extra_data['function_kwargs'] = kwargs
                            
                            if include_result:
                                extra_data['result'] = result
                            
                            getattr(logger, level.value.lower())(log_message, extra=extra_data)
                        
                        return result
                        
                except Exception as e:
                    execution_time = (time.perf_counter() - start_time) * 1000
                    logger.error(
                        f"Function {func.__name__} failed after {execution_time:.2f}ms",
                        extra={
                            'execution_time_ms': execution_time,
                            'error': str(e),
                            'error_type': type(e).__name__
                        },
                        exc_info=True
                    )
                    raise
            
            return sync_wrapper
    
    return decorator


def log_errors(
    logger_name: str = None,
    level: LogLevel = LogLevel.ERROR,
    reraise: bool = True,
    include_args: bool = True
):
    """
    记录函数错误的装饰器
    
    Args:
        logger_name: 日志器名称
        level: 日志级别
        reraise: 是否重新抛出异常
        include_args: 是否包含参数信息
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger_name
        if logger_name is None:
            logger_name = func.__module__
        
        logger = LoggerFactory.get_logger(logger_name)
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    extra_data = {
                        'function': func.__name__,
                        'error_type': type(e).__name__
                    }
                    
                    if include_args:
                        extra_data['function_args'] = args
                        extra_data['function_kwargs'] = kwargs
                    
                    getattr(logger, level.value.lower())(
                        f"Error in {func.__name__}: {e}",
                        extra=extra_data,
                        exc_info=True
                    )
                    
                    if reraise:
                        raise
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    extra_data = {
                        'function': func.__name__,
                        'error_type': type(e).__name__
                    }
                    
                    if include_args:
                        extra_data['function_args'] = args
                        extra_data['function_kwargs'] = kwargs
                    
                    getattr(logger, level.value.lower())(
                        f"Error in {func.__name__}: {e}",
                        extra=extra_data,
                        exc_info=True
                    )
                    
                    if reraise:
                        raise
            
            return sync_wrapper
    
    return decorator


def log_method_calls(
    logger_name: str = None,
    level: LogLevel = LogLevel.DEBUG,
    include_args: bool = False,
    include_result: bool = False,
    exclude_methods: list = None
):
    """
    记录类方法调用的装饰器
    
    Args:
        logger_name: 日志器名称
        level: 日志级别
        include_args: 是否包含参数信息
        include_result: 是否包含返回结果
        exclude_methods: 排除的方法名列表
    """
    if exclude_methods is None:
        exclude_methods = ['__init__', '__repr__', '__str__', '__hash__', '__eq__']
    
    def decorator(cls):
        # 获取日志器
        nonlocal logger_name
        if logger_name is None:
            logger_name = cls.__module__
        
        logger = LoggerFactory.get_logger(logger_name)
        
        # 装饰所有方法
        for name in dir(cls):
            if name in exclude_methods or name.startswith('_'):
                continue
            
            attr = getattr(cls, name)
            if callable(attr) and not isinstance(attr, type):
                # 装饰方法
                if asyncio.iscoroutinefunction(attr):
                    async def make_async_logged_method(method, method_name):
                        @functools.wraps(method)
                        async def logged_method(self, *args, **kwargs):
                            extra_data = {
                                'class': cls.__name__,
                                'method': method_name,
                                'instance_id': id(self)
                            }
                            
                            if include_args:
                                extra_data['function_args'] = args
                                extra_data['function_kwargs'] = kwargs
                            
                            getattr(logger, level.value.lower())(
                                f"Calling {cls.__name__}.{method_name}",
                                extra=extra_data
                            )
                            
                            try:
                                result = await method(self, *args, **kwargs)
                                
                                if include_result:
                                    extra_data['result'] = result
                                
                                getattr(logger, level.value.lower())(
                                    f"Completed {cls.__name__}.{method_name}",
                                    extra=extra_data
                                )
                                
                                return result
                            except Exception as e:
                                logger.error(
                                    f"Error in {cls.__name__}.{method_name}: {e}",
                                    extra={**extra_data, 'error_type': type(e).__name__},
                                    exc_info=True
                                )
                                raise
                        
                        return logged_method
                    
                    setattr(cls, name, make_async_logged_method(attr, name))
                else:
                    def make_logged_method(method, method_name):
                        @functools.wraps(method)
                        def logged_method(self, *args, **kwargs):
                            extra_data = {
                                'class': cls.__name__,
                                'method': method_name,
                                'instance_id': id(self)
                            }
                            
                            if include_args:
                                extra_data['function_args'] = args
                                extra_data['function_kwargs'] = kwargs
                            
                            getattr(logger, level.value.lower())(
                                f"Calling {cls.__name__}.{method_name}",
                                extra=extra_data
                            )
                            
                            try:
                                result = method(self, *args, **kwargs)
                                
                                if include_result:
                                    extra_data['result'] = result
                                
                                getattr(logger, level.value.lower())(
                                    f"Completed {cls.__name__}.{method_name}",
                                    extra=extra_data
                                )
                                
                                return result
                            except Exception as e:
                                logger.error(
                                    f"Error in {cls.__name__}.{method_name}: {e}",
                                    extra={**extra_data, 'error_type': type(e).__name__},
                                    exc_info=True
                                )
                                raise
                        
                        return logged_method
                    
                    setattr(cls, name, make_logged_method(attr, name))
        
        return cls
    
    return decorator


@contextmanager
def log_operation(
    operation_name: str,
    logger_name: str = None,
    level: LogLevel = LogLevel.INFO,
    log_start: bool = True,
    log_end: bool = True,
    log_duration: bool = True
):
    """
    记录操作执行的上下文管理器
    
    Args:
        operation_name: 操作名称
        logger_name: 日志器名称
        level: 日志级别
        log_start: 是否记录开始
        log_end: 是否记录结束
        log_duration: 是否记录持续时间
    """
    # 获取调用者信息
    if logger_name is None:
        frame = inspect.currentframe().f_back
        logger_name = frame.f_globals.get('__name__', 'unknown')
    
    logger = LoggerFactory.get_logger(logger_name)
    start_time = time.perf_counter()
    
    # 记录开始
    if log_start:
        getattr(logger, level.value.lower())(
            f"Starting operation: {operation_name}",
            extra={'operation': operation_name, 'status': 'started'}
        )
    
    try:
        with log_context(operation=operation_name):
            yield
        
        # 记录成功结束
        end_time = time.perf_counter()
        duration = (end_time - start_time) * 1000
        
        extra_data = {'operation': operation_name, 'status': 'completed'}
        if log_duration:
            extra_data['duration_ms'] = duration
        
        if log_end:
            getattr(logger, level.value.lower())(
                f"Completed operation: {operation_name}" + 
                (f" in {duration:.2f}ms" if log_duration else ""),
                extra=extra_data
            )
    
    except Exception as e:
        # 记录失败
        end_time = time.perf_counter()
        duration = (end_time - start_time) * 1000
        
        logger.error(
            f"Failed operation: {operation_name} after {duration:.2f}ms",
            extra={
                'operation': operation_name,
                'status': 'failed',
                'duration_ms': duration,
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        raise


def log_deprecated(
    reason: str = None,
    alternative: str = None,
    logger_name: str = None,
    level: LogLevel = LogLevel.WARNING
):
    """
    标记函数为已弃用的装饰器
    
    Args:
        reason: 弃用原因
        alternative: 替代方案
        logger_name: 日志器名称
        level: 日志级别
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger_name
        if logger_name is None:
            logger_name = func.__module__
        
        logger = LoggerFactory.get_logger(logger_name)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = f"Function {func.__name__} is deprecated"
            if reason:
                message += f": {reason}"
            if alternative:
                message += f". Use {alternative} instead"
            
            getattr(logger, level.value.lower())(
                message,
                extra={
                    'deprecated_function': func.__name__,
                    'reason': reason,
                    'alternative': alternative
                }
            )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator