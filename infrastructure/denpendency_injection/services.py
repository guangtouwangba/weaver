"""
服务配置模块

统一配置所有服务的依赖注入，包括：
- 基础设施服务（数据库、缓存、消息队列等）
- 应用服务（控制器、应用服务等）
- 第三方服务集成
"""

import logging
from typing import Optional

from .registry import get_registry
from .event_bus_factory import create_event_bus

# 导入实际类型以支持Registry的自动依赖解析
from sqlalchemy.ext.asyncio import AsyncSession
from application.event.event_bus import EventBus
from infrastructure.storage.interfaces import IObjectStorage
from application.topic.topic import TopicController
from application.file.file_upload import FileApplication
from ..database.repositories.file import FileRepository, UploadSessionRepository

logger = logging.getLogger(__name__)


async def configure_infrastructure_services():
    """
    配置基础设施层服务
    
    包括：
    - EventBus（事件总线）
    - Database Session（数据库会话）
    - Object Storage（对象存储）
    - Cache（缓存）
    """
    registry = get_registry()
    
    # EventBus - 单例模式
    # 全局唯一的事件总线，在整个应用生命周期中共享
    from application.event.event_bus import EventBus
    registry.register_singleton(EventBus, create_event_bus)
    logger.debug("Registered EventBus as singleton")
    
    # Database Session - 作用域模式（请求级别）
    # 每个HTTP请求使用独立的数据库会话，确保事务隔离
    from infrastructure.database import get_async_database_session
    from sqlalchemy.ext.asyncio import AsyncSession
    registry.register_scoped(AsyncSession, get_async_database_session)
    logger.debug("Registered AsyncSession as scoped")
    
    # Object Storage - 单例模式
    # 存储服务可以全局共享，底层连接池管理并发
    from infrastructure.storage.factory import create_storage_from_env
    from infrastructure.storage.interfaces import IObjectStorage
    registry.register_singleton(IObjectStorage, create_storage_from_env)
    logger.debug("Registered IObjectStorage as singleton")


async def configure_application_services():
    """
    配置应用层服务
    
    包括：
    - TopicController
    - FileApplication
    - 其他应用控制器
    """
    registry = get_registry()
    
    # TopicController - 临时模式，支持依赖注入
    from application.topic.topic import TopicController
    registry.register_factory(TopicController, create_topic_controller_with_di)
    logger.debug("Registered TopicController as transient with DI")
    
    # FileApplication - 临时模式，支持依赖注入
    from application.file.file_upload import FileApplication
    registry.register_factory(FileApplication, create_file_application_with_di)
    logger.debug("Registered FileApplication as transient with DI")


# ========== 支持依赖注入的工厂函数 ==========

async def create_topic_controller_with_di(
    session: AsyncSession,  # 自动注入数据库会话
    event_bus: EventBus,    # 自动注入事件总线
    storage: IObjectStorage  # 自动注入存储服务
) -> TopicController:
    """
    创建TopicController，所有依赖自动注入
    
    Args:
        session: 数据库会话（作用域级别，每个请求独立）
        event_bus: 事件总线（单例，全局共享）
        storage: 对象存储服务（单例，全局共享）
        
    Returns:
        配置完整的TopicController实例
    """
    from application.topic.topic import TopicController
    from infrastructure.database.repositories.topic import (
        TopicRepository, TagRepository, TopicResourceRepository, ConversationRepository
    )
    from infrastructure.storage.minio_storage import MinIOFileManager
    from infrastructure.config import get_config
    
    # 获取配置
    config = get_config()
    
    # 创建repositories（使用注入的数据库会话）
    topic_repo = TopicRepository(session)
    tag_repo = TagRepository(session)
    resource_repo = TopicResourceRepository(session)
    conversation_repo = ConversationRepository(session)
    
    # 创建文件管理器（使用注入的存储服务）
    file_manager = MinIOFileManager(storage, config.storage.default_bucket)
    
    # 创建应用服务（使用注入的依赖）
    from application.topic.topic import TopicApplicationService
    app_service = TopicApplicationService(
        topic_repo=topic_repo,
        tag_repo=tag_repo,
        resource_repo=resource_repo,
        conversation_repo=conversation_repo,
        message_broker=None,  # 暂时不使用message_broker
        storage=storage,
        file_manager=file_manager
    )
    
    # 创建控制器
    controller = TopicController(app_service)
    
    logger.debug("Created TopicController with injected dependencies")
    return controller


async def create_file_application_with_di(
    event_bus: EventBus,           # 自动注入事件总线
    storage: IObjectStorage,       # 自动注入存储服务
    session: AsyncSession          # 自动注入数据库会话
) -> FileApplication:
    """
    创建FileApplication，所有依赖自动注入
    
    Args:
        event_bus: 事件总线（单例，全局共享）
        storage: 对象存储服务（单例，全局共享）
        session: 数据库会话（作用域级别，每个请求独立）
        
    Returns:
        配置完整的FileApplication实例
    """
    from application.file.file_upload import FileApplication
    from services.fileupload_services import FileUploadService, FileAccessService
    from infrastructure.config import get_config

    # 获取配置
    config = get_config()
    
    # 创建Mock repository实现（实现了Domain接口）
    # 注意：这是临时解决方案，实际项目中应该使用真正的数据库Repository
    file_repository = FileRepository(session)
    upload_session_repository = UploadSessionRepository(session)
    
    # 创建服务实例（使用注入的依赖）
    upload_service = FileUploadService(
        storage=storage,
        file_repository=file_repository,  # 使用Domain接口
        upload_session_repository=upload_session_repository,  # 使用Domain接口
        default_bucket=config.storage.default_bucket
    )
    
    access_service = FileAccessService(
        storage=storage,
        file_repository=file_repository  # 使用Domain接口
    )
    
    # 创建应用实例
    application = FileApplication(upload_service, access_service, event_bus)
    
    logger.debug("Created FileApplication with proper Repository pattern dependencies")
    return application


async def configure_all_services():
    """
    配置所有服务依赖
    
    这是主要的配置入口点，应该在应用启动时调用
    """
    logger.info("Starting service dependency configuration...")
    
    try:
        # 1. 先配置基础设施服务
        await configure_infrastructure_services()
        logger.info("Infrastructure services configured")
        
        # 2. 再配置应用服务（可能依赖基础设施服务）
        await configure_application_services()
        logger.info("Application services configured")
        
        # 3. 验证关键服务是否正确注册
        registry = get_registry()
        critical_services = [
            'EventBus',
            'AsyncSession', 
            'IObjectStorage',
            'TopicController',
            'FileApplication'
        ]
        
        registered_services = registry.get_registered_services()
        missing_services = []
        
        for service_name in critical_services:
            found = any(service_type.__name__ == service_name for service_type in registered_services.keys())
            if not found:
                missing_services.append(service_name)
        
        if missing_services:
            logger.warning(f"Some critical services not registered: {missing_services}")
        else:
            logger.info("All critical services registered successfully")
        
        logger.info(f"Service configuration completed. Total services: {len(registered_services)}")
        
    except Exception as e:
        logger.error(f"Failed to configure services: {e}")
        raise


async def cleanup_services():
    """
    清理所有服务资源
    
    应该在应用关闭时调用
    """
    logger.info("Starting service cleanup...")
    
    try:
        registry = get_registry()
        await registry.cleanup()
        logger.info("Service cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during service cleanup: {e}")


def get_service_status() -> dict:
    """
    获取服务注册状态信息
    
    Returns:
        包含服务注册信息的字典
    """
    registry = get_registry()
    registered_services = registry.get_registered_services()
    
    status = {
        "total_services": len(registered_services),
        "services": {
            service_type.__name__: {
                "scope": scope.value,
                "module": service_type.__module__
            }
            for service_type, scope in registered_services.items()
        }
    }
    
    return status