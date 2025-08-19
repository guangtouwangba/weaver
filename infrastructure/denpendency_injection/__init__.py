
"""
Dependency Injection Module

提供轻量级的依赖注入系统，专为FastAPI设计。

主要组件：
- DependencyRegistry: 核心依赖注册器
- FastAPI集成: 与FastAPI的Depends()机制无缝集成
- 服务配置: 统一的服务注册配置
- Event Bus Factory: 事件总线工厂
"""

# 核心Registry组件
from .registry import (
    DependencyRegistry, 
    ServiceScope, 
    get_registry, 
    reset_registry
)

# FastAPI集成组件
from .fastapi_integration import (
    get_service,
    get_dependency_registry,
    setup_fastapi_integration,
    ScopeCleanupMiddleware,
    # 便捷依赖函数
    get_event_bus,
    get_topic_controller,
    get_file_application,
    # 预配置的Depends
    DependsEventBus,
    DependsTopicController,
    DependsFileApplication
)

# 服务配置组件
from .services import (
    configure_all_services,
    configure_infrastructure_services,
    configure_application_services,
    cleanup_services,
    get_service_status
)

# 事件总线工厂（保持向后兼容）
from .event_bus_factory import create_event_bus

__all__ = [
    # 核心Registry
    "DependencyRegistry",
    "ServiceScope", 
    "get_registry",
    "reset_registry",
    
    # FastAPI集成
    "get_service",
    "get_dependency_registry", 
    "setup_fastapi_integration",
    "ScopeCleanupMiddleware",
    
    # 便捷依赖函数
    "get_event_bus",
    "get_topic_controller", 
    "get_file_application",
    
    # 预配置的Depends
    "DependsEventBus",
    "DependsTopicController",
    "DependsFileApplication",
    
    # 服务配置
    "configure_all_services",
    "configure_infrastructure_services",
    "configure_application_services", 
    "cleanup_services",
    "get_service_status",
    
    # 事件总线（向后兼容）
    "create_event_bus",
]

