"""
任务装饰器模块

提供任务执行相关的装饰器功能
"""

import logging
import time
import functools
from typing import Callable, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def log_execution_time(threshold_ms: int = 1000):
    """
    记录任务执行时间的装饰器
    
    Args:
        threshold_ms: 阈值(毫秒)，超过此时间会记录警告日志
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                end_time = time.time()
                execution_time_ms = (end_time - start_time) * 1000
                
                if execution_time_ms > threshold_ms:
                    logger.warning(
                        f"Task {func.__name__} execution time: {execution_time_ms:.2f}ms "
                        f"(exceeded threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(
                        f"Task {func.__name__} execution time: {execution_time_ms:.2f}ms"
                    )
                
                return result
                
            except Exception as e:
                end_time = time.time()
                execution_time_ms = (end_time - start_time) * 1000
                
                logger.error(
                    f"Task {func.__name__} failed after {execution_time_ms:.2f}ms: {e}"
                )
                raise
        
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay_seconds: float = 1.0):
    """
    失败重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay_seconds: 重试间隔(秒)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"Task {func.__name__} succeeded on attempt {attempt + 1}")
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Task {func.__name__} failed on attempt {attempt + 1}/{max_retries + 1}: {e}"
                            f" Retrying in {delay_seconds} seconds..."
                        )
                        
                        import asyncio
                        await asyncio.sleep(delay_seconds)
                    else:
                        logger.error(
                            f"Task {func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
            
            # 如果所有重试都失败了，抛出最后的异常
            raise last_exception
        
        return wrapper
    return decorator


def task_context_manager(task_name: str = None):
    """
    任务上下文管理装饰器
    
    Args:
        task_name: 任务名称
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            actual_task_name = task_name or func.__name__
            
            logger.info(f"Starting task: {actual_task_name}")
            start_time = datetime.utcnow()
            
            try:
                result = await func(*args, **kwargs)
                
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"Completed task: {actual_task_name} (duration: {duration:.2f}s)")
                return result
                
            except Exception as e:
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                logger.error(f"Failed task: {actual_task_name} (duration: {duration:.2f}s): {e}")
                raise
        
        return wrapper
    return decorator


logger.info("任务装饰器模块已加载")
