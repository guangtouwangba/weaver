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
from application.event.event_bus import EventBus
from infrastructure.storage.interfaces import IObjectStorage

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
    try:
        from infrastructure.database import get_async_database_session
        from sqlalchemy.ext.asyncio import AsyncSession as SQLAsyncSession
        registry.register_scoped(SQLAsyncSession, get_async_database_session)
        logger.debug("Registered AsyncSession as scoped")
    except ImportError as e:
        logger.warning(f"SQLAlchemy AsyncSession not available: {e}")
        # 注册一个mock session以便应用可以启动
        async def mock_session():
            logger.warning("Using mock database session - some features may not work")
            return None
        from typing import Any
        registry.register_scoped(type(None), mock_session)
        logger.debug("Registered mock session")
    
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
    - Event Handlers
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
    
    # KnowledgeOrchestrationService - 单例模式
    from services.knowledge_orchestration import KnowledgeOrchestrationService
    registry.register_factory(KnowledgeOrchestrationService, create_knowledge_orchestration_service_with_di)
    logger.debug("Registered KnowledgeOrchestrationService as singleton with DI")
    
    # FileUploadConfirmedHandler - 单例模式
    from application.event.handlers.file_upload_confirmed_handler import FileUploadConfirmedHandler
    registry.register_factory(FileUploadConfirmedHandler, create_file_upload_confirmed_handler_with_di)
    logger.debug("Registered FileUploadConfirmedHandler as singleton with DI")


# ========== 支持依赖注入的工厂函数 ==========

async def create_topic_controller_with_di():
    """
    创建TopicController，手动获取所有依赖
    """
    from application.topic.topic import TopicController
    from infrastructure.database.repositories.topic import (
        TopicRepository, TagRepository, TopicResourceRepository, ConversationRepository
    )
    from infrastructure.storage.minio_storage import MinIOFileManager
    from infrastructure.config import get_config
    from infrastructure.denpendency_injection.registry import get_registry
    
    # 手动获取依赖
    registry = get_registry()
    
    try:
        # 获取事件总线
        event_bus = await registry.get(EventBus)
        
        # 获取存储服务
        storage = await registry.get(IObjectStorage)
        
        # 获取数据库会话
        try:
            from sqlalchemy.ext.asyncio import AsyncSession as SQLAsyncSession
            session = await registry.get(SQLAsyncSession)
        except Exception as e:
            logger.error(f"Failed to get database session: {e}")
            raise ValueError("Database session is required for TopicController")
        
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
        
    except Exception as e:
        logger.error(f"Failed to create TopicController: {e}")
        raise


async def create_file_application_with_di():
    """
    创建FileApplication，手动获取所有依赖
    """
    from application.file.file_upload import FileApplication
    from services.fileupload_services import FileUploadService, FileAccessService
    from infrastructure.config import get_config
    from infrastructure.denpendency_injection.registry import get_registry

    # 手动获取依赖
    registry = get_registry()
    
    try:
        # 获取事件总线
        event_bus = await registry.get(EventBus)
        
        # 获取存储服务
        storage = await registry.get(IObjectStorage)
        
        # 获取数据库会话
        try:
            from sqlalchemy.ext.asyncio import AsyncSession as SQLAsyncSession
            session = await registry.get(SQLAsyncSession)
        except Exception as e:
            logger.error(f"Failed to get database session: {e}")
            raise ValueError("Database session is required for FileApplication")
        
        # 获取配置
        config = get_config()
        
        # 创建Repository实现
        from infrastructure.database.repositories.file import FileRepository, UploadSessionRepository
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
        
    except Exception as e:
        logger.error(f"Failed to create FileApplication: {e}")
        raise


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
        
        # 3. 配置并注册事件处理器
        await configure_event_handlers()
        logger.info("Event handlers configured")
        
        # 4. 验证关键服务是否正确注册
        registry = get_registry()
        critical_services = [
            'EventBus',
            'AsyncSession', 
            'IObjectStorage',
            'TopicController',
            'FileApplication',
            'KnowledgeOrchestrationService',
            'FileUploadConfirmedHandler'
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


async def create_knowledge_orchestration_service_with_di():
    """
    创建KnowledgeOrchestrationService，手动获取所有依赖
    """
    from services.knowledge_orchestration import KnowledgeOrchestrationService
    from infrastructure.knowledge.implementations import (
        DatabaseKnowledgeRepository, RAGEngineDocumentProcessor, 
        OpenAIVectorService, HybridSearchService
    )
    from infrastructure.database.repositories.file import FileRepository
    from infrastructure.config import get_config
    from infrastructure.denpendency_injection.registry import get_registry
    
    # 手动获取依赖
    registry = get_registry()
    
    try:
        # 获取事件总线
        event_bus = await registry.get(EventBus)
        
        # 获取存储服务
        storage = await registry.get(IObjectStorage)
        
        # 获取数据库会话
        try:
            from sqlalchemy.ext.asyncio import AsyncSession as SQLAsyncSession
            session = await registry.get(SQLAsyncSession)
        except Exception as e:
            logger.error(f"Failed to get database session: {e}")
            raise ValueError("Database session is required for KnowledgeOrchestrationService")
        
        config = get_config()
        
        # 创建Repository实现
        file_repository = FileRepository(session)
        knowledge_repository = DatabaseKnowledgeRepository(file_repository, storage)
        
        # 创建处理器实现
        document_processor = RAGEngineDocumentProcessor(storage)
        
        # 创建向量服务实现
        vector_service = OpenAIVectorService(api_key=config.openai.api_key if hasattr(config, 'openai') else "")
        
        # 创建搜索服务实现
        search_service = HybridSearchService(vector_service, knowledge_repository)
        
        # 创建编排服务
        orchestration_service = KnowledgeOrchestrationService(
            knowledge_repository=knowledge_repository,
            document_processor=document_processor,
            vector_service=vector_service,
            search_service=search_service,
            event_bus=event_bus
        )
        
        logger.debug("Created KnowledgeOrchestrationService with injected dependencies")
        return orchestration_service
        
    except Exception as e:
        logger.error(f"Failed to create KnowledgeOrchestrationService: {e}")
        raise


async def create_file_upload_confirmed_handler_with_di():
    """
    创建FileUploadConfirmedHandler，手动获取所有依赖
    """
    from application.event.handlers.file_upload_confirmed_handler import FileUploadConfirmedHandler
    from infrastructure.denpendency_injection.registry import get_registry
    
    # 手动获取依赖
    registry = get_registry()
    
    try:
        # 获取事件总线
        event_bus = await registry.get(EventBus)
        
        # 获取KnowledgeOrchestrationService实例
        knowledge_orchestration_service = await create_knowledge_orchestration_service_with_di()
        
        # 创建事件处理器
        handler = FileUploadConfirmedHandler(
            knowledge_orchestration_service=knowledge_orchestration_service,
            event_bus=event_bus
        )
        
        logger.debug("Created FileUploadConfirmedHandler with injected dependencies")
        return handler
        
    except Exception as e:
        logger.error(f"Failed to create FileUploadConfirmedHandler: {e}")
        raise


async def configure_event_handlers():
    """
    配置和注册事件处理器
    
    这个函数应该在应用启动时调用，用于注册所有事件处理器到事件总线
    """
    registry = get_registry()
    
    try:
        # 获取事件总线
        event_bus = await registry.get(EventBus)
        
        # 获取并注册FileUploadConfirmedHandler
        from application.event.handlers.file_upload_confirmed_handler import FileUploadConfirmedHandler
        file_upload_handler = await registry.get(FileUploadConfirmedHandler)
        event_bus.subscribe(file_upload_handler)
        logger.info("Registered FileUploadConfirmedHandler to EventBus")
        
        # 在这里添加其他事件处理器的注册
        # document_processing_handler = await registry.get(DocumentProcessingHandler)
        # event_bus.subscribe(document_processing_handler)
        
        logger.info("All event handlers registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to configure event handlers: {e}")
        raise