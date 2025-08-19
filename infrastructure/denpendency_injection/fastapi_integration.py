"""
FastAPI集成模块

提供Registry与FastAPI的无缝集成，包括：
- 自动依赖注入
- 请求作用域管理
- 中间件集成
- 异常处理
"""

import logging
from typing import TypeVar, Callable, Any
from fastapi import Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from .registry import get_registry, DependencyRegistry

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def get_dependency_registry() -> DependencyRegistry:
    """
    FastAPI依赖函数 - 获取全局注册器
    
    Returns:
        DependencyRegistry: 全局依赖注册器实例
    """
    return get_registry()


def get_service(service_type: type) -> Callable:
    """
    为指定服务类型创建FastAPI依赖函数
    
    这是核心的集成函数，它：
    1. 创建一个FastAPI依赖函数
    2. 自动提取请求作用域标识符
    3. 调用Registry获取服务实例
    4. 处理依赖注入异常
    
    Args:
        service_type: 需要注入的服务类型
        
    Returns:
        FastAPI依赖函数
        
    Example:
        ```python
        @app.get("/topics")
        async def get_topics(
            controller: TopicController = Depends(get_service(TopicController))
        ):
            return await controller.get_all_topics()
        ```
    """
    
    async def dependency(
        request: Request,
        registry: DependencyRegistry = Depends(get_dependency_registry)
    ) -> T:
        """
        FastAPI依赖函数实现
        
        Args:
            request: FastAPI请求对象
            registry: 依赖注册器
            
        Returns:
            请求的服务实例
            
        Raises:
            HTTPException: 当依赖解析失败时
        """
        try:
            # 使用请求对象的ID作为作用域标识符
            # 这确保每个HTTP请求都有独立的作用域
            scope_id = str(id(request))
            
            # 从注册器获取服务实例
            instance = await registry.get(service_type, scope_id=scope_id)
            
            logger.debug(f"Resolved {service_type.__name__} for request {scope_id}")
            return instance
            
        except ValueError as e:
            # 服务未注册或循环依赖
            logger.error(f"Dependency resolution failed for {service_type.__name__}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Service dependency error: {str(e)}"
            )
        except Exception as e:
            # 其他意外错误
            logger.error(f"Unexpected error resolving {service_type.__name__}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal service error"
            )
    
    # 设置函数名称，方便调试
    dependency.__name__ = f"get_{service_type.__name__.lower()}_dependency"
    
    return dependency


class ScopeCleanupMiddleware:
    """
    请求作用域清理中间件
    
    在每个HTTP请求结束后自动清理该请求的作用域实例，
    防止内存泄漏。
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # 创建请求对象以获取作用域ID
        request = Request(scope, receive)
        scope_id = str(id(request))
        
        try:
            # 处理请求
            await self.app(scope, receive, send)
        finally:
            # 请求结束后清理作用域
            try:
                registry = get_registry()
                registry.clear_scope(scope_id)
                logger.debug(f"Cleaned up scope {scope_id}")
            except Exception as e:
                logger.warning(f"Error cleaning up scope {scope_id}: {e}")


def setup_fastapi_integration(app):
    """
    配置FastAPI应用的Registry集成
    
    Args:
        app: FastAPI应用实例
    """
    # 添加作用域清理中间件
    app.add_middleware(ScopeCleanupMiddleware)
    
    # 添加异常处理器
    @app.exception_handler(ValueError)
    async def dependency_error_handler(request: Request, exc: ValueError):
        """处理依赖注入相关的ValueError"""
        if "not registered" in str(exc) or "circular dependency" in str(exc).lower():
            logger.error(f"Dependency injection error: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Service Configuration Error",
                    "message": "A required service is not properly configured",
                    "detail": str(exc) if logger.level <= logging.DEBUG else None
                }
            )
        # 其他ValueError继续传播
        raise exc
    
    logger.info("FastAPI Registry integration configured")


# 便捷函数，用于常见的服务类型
def get_event_bus():
    """获取EventBus依赖函数"""
    from application.event.event_bus import EventBus
    return get_service(EventBus)


def get_topic_controller():
    """获取TopicController依赖函数"""
    from application.topic.topic import TopicController
    return get_service(TopicController)


def get_file_application():
    """获取FileApplication依赖函数"""
    from application.file.file_upload import FileApplication
    return get_service(FileApplication)


# 类型别名，方便使用
DependsEventBus = Depends(get_event_bus())
DependsTopicController = Depends(get_topic_controller())
DependsFileApplication = Depends(get_file_application())