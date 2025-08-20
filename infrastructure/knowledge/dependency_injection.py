"""
Knowledge Management Dependency Injection

知识管理模块的依赖注入配置，负责：
1. 将Domain接口绑定到Infrastructure实现
2. 配置服务生命周期
3. 管理依赖关系
4. 环境相关的配置

遵循依赖倒置原则，上层不依赖下层的具体实现。
"""

import logging
from typing import Optional

# Dependency injection framework
from infrastructure.denpendency_injection.registry import get_registry

# Domain interfaces
from domain.knowledge import (
    IKnowledgeRepository, IDocumentProcessor, IVectorService, ISearchService
)

# Infrastructure implementations
from .implementations import (
    DatabaseKnowledgeRepository, RAGEngineDocumentProcessor, 
    OpenAIVectorService, HybridSearchService
)

# Services
from services.knowledge_orchestration import KnowledgeOrchestrationService, KnowledgeWorkflowService

# External dependencies
from infrastructure.database.repositories.file import FileRepository
from infrastructure.storage.interfaces import IObjectStorage
from application.event.event_bus import EventBus
from infrastructure.config import get_config

logger = logging.getLogger(__name__)


async def configure_knowledge_services():
    """
    配置知识管理相关的所有服务
    
    按照依赖关系顺序注册服务：
    Infrastructure -> Domain Services -> Application Services
    """
    logger.info("Configuring knowledge management services...")
    
    registry = get_registry()
    config = get_config()
    
    try:
        # 1. 注册Repository实现
        await _configure_repositories(registry)
        
        # 2. 注册Domain Service实现
        await _configure_domain_services(registry, config)
        
        # 3. 注册Application Services
        await _configure_application_services(registry)
        
        # 4. 验证注册
        await _validate_service_registration(registry)
        
        logger.info("Knowledge management services configured successfully")
        
    except Exception as e:
        logger.error(f"Failed to configure knowledge services: {e}")
        raise


async def _configure_repositories(registry):
    """配置Repository层"""
    
    # DatabaseKnowledgeRepository - 作用域级别（每个请求独立）
    async def create_knowledge_repository(
        file_repository: FileRepository,
        storage: IObjectStorage
    ) -> IKnowledgeRepository:
        """创建知识仓储实例"""
        return DatabaseKnowledgeRepository(file_repository, storage)
    
    registry.register_factory(IKnowledgeRepository, create_knowledge_repository)
    logger.debug("Registered IKnowledgeRepository")


async def _configure_domain_services(registry, config):
    """配置Domain Service层"""
    
    # RAGEngineDocumentProcessor - 单例模式
    async def create_document_processor(storage: IObjectStorage) -> IDocumentProcessor:
        """创建文档处理器实例"""
        return RAGEngineDocumentProcessor(storage)
    
    registry.register_factory(IDocumentProcessor, create_document_processor)
    logger.debug("Registered IDocumentProcessor")
    
    # OpenAIVectorService - 单例模式
    async def create_vector_service() -> IVectorService:
        """创建向量服务实例"""
        api_key = config.openai.api_key if hasattr(config, 'openai') else "mock_key"
        return OpenAIVectorService(api_key)
    
    registry.register_singleton(IVectorService, create_vector_service)
    logger.debug("Registered IVectorService")
    
    # HybridSearchService - 单例模式
    async def create_search_service(
        vector_service: IVectorService,
        knowledge_repository: IKnowledgeRepository
    ) -> ISearchService:
        """创建搜索服务实例"""
        return HybridSearchService(vector_service, knowledge_repository)
    
    registry.register_factory(ISearchService, create_search_service)
    logger.debug("Registered ISearchService")


async def _configure_application_services(registry):
    """配置Application Service层"""
    
    # KnowledgeOrchestrationService - 作用域级别
    async def create_orchestration_service(
        knowledge_repository: IKnowledgeRepository,
        document_processor: IDocumentProcessor,
        vector_service: IVectorService,
        search_service: ISearchService,
        event_bus: EventBus
    ) -> KnowledgeOrchestrationService:
        """创建编排服务实例"""
        return KnowledgeOrchestrationService(
            knowledge_repository=knowledge_repository,
            document_processor=document_processor,
            vector_service=vector_service,
            search_service=search_service,
            event_bus=event_bus
        )
    
    registry.register_factory(KnowledgeOrchestrationService, create_orchestration_service)
    logger.debug("Registered KnowledgeOrchestrationService")
    
    # KnowledgeWorkflowService - 作用域级别
    async def create_workflow_service(
        orchestration_service: KnowledgeOrchestrationService
    ) -> KnowledgeWorkflowService:
        """创建工作流服务实例"""
        return KnowledgeWorkflowService(orchestration_service)
    
    registry.register_factory(KnowledgeWorkflowService, create_workflow_service)
    logger.debug("Registered KnowledgeWorkflowService")


async def _validate_service_registration(registry):
    """验证关键服务是否正确注册"""
    
    critical_services = [
        IKnowledgeRepository,
        IDocumentProcessor,
        IVectorService,
        ISearchService,
        KnowledgeOrchestrationService,
        KnowledgeWorkflowService
    ]
    
    registered_services = registry.get_registered_services()
    missing_services = []
    
    for service_type in critical_services:
        if service_type not in registered_services:
            missing_services.append(service_type.__name__)
    
    if missing_services:
        raise RuntimeError(f"Critical knowledge services not registered: {missing_services}")
    
    logger.info(f"Validated {len(critical_services)} critical knowledge services")


# 便捷函数用于获取服务实例
async def get_knowledge_orchestration_service() -> KnowledgeOrchestrationService:
    """获取知识编排服务实例"""
    registry = get_registry()
    return await registry.get(KnowledgeOrchestrationService)


async def get_knowledge_workflow_service() -> KnowledgeWorkflowService:
    """获取知识工作流服务实例"""
    registry = get_registry()
    return await registry.get(KnowledgeWorkflowService)


# Mock服务配置（用于测试和开发）
class MockKnowledgeServices:
    """
    Mock知识服务配置
    
    用于测试环境或开发阶段，提供轻量级的服务实现。
    """
    
    @staticmethod
    async def configure_mock_services():
        """配置Mock服务"""
        from .mocks import (
            MockKnowledgeRepository, MockDocumentProcessor,
            MockVectorService, MockSearchService
        )
        
        registry = get_registry()
        
        # 注册Mock实现
        registry.register_singleton(IKnowledgeRepository, lambda: MockKnowledgeRepository())
        registry.register_singleton(IDocumentProcessor, lambda: MockDocumentProcessor())
        registry.register_singleton(IVectorService, lambda: MockVectorService())
        registry.register_singleton(ISearchService, lambda: MockSearchService())
        
        logger.info("Mock knowledge services configured")


# 环境配置
async def configure_knowledge_services_for_environment(environment: str = "development"):
    """
    根据环境配置知识服务
    
    Args:
        environment: 环境名称 (development, testing, production)
    """
    if environment == "testing":
        await MockKnowledgeServices.configure_mock_services()
    else:
        await configure_knowledge_services()
    
    logger.info(f"Knowledge services configured for {environment} environment")