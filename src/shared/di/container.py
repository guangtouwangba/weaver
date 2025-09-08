"""
Dependency injection container.

Manages the creation and lifecycle of application dependencies.
"""

from typing import Optional, Dict, Any
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

# Core imports
from ...core.repositories.document_repository import DocumentRepository
from ...core.repositories.topic_repository import TopicRepository
from ...core.repositories.chat_repository import ChatRepository
from ...core.repositories.file_repository import FileRepository

# Use case imports
from ...use_cases.document.create_document import CreateDocumentUseCase
from ...use_cases.document.get_document import GetDocumentUseCase
from ...use_cases.document.search_documents import SearchDocumentsUseCase
from ...use_cases.document.process_file import ProcessFileUseCase
from ...use_cases.chat.start_chat_session import StartChatSessionUseCase
from ...use_cases.chat.send_message import SendMessageUseCase
from ...use_cases.knowledge.create_topic import CreateTopicUseCase
from ...use_cases.knowledge.get_topic import GetTopicUseCase

# Adapter imports
from ...adapters.repositories.memory_document_repository import MemoryDocumentRepository
from ...adapters.repositories.memory_topic_repository import MemoryTopicRepository
from ...adapters.repositories.memory_chat_repository import MemoryChatRepository
from ...adapters.ai.openai_adapter import OpenAIAdapter


class Container(containers.DeclarativeContainer):
    """Main dependency injection container."""
    
    # Configuration
    config = providers.Configuration()
    
    # Infrastructure
    database_session = providers.Dependency(instance_of=AsyncSession)
    
    # AI Services
    ai_service = providers.Singleton(
        OpenAIAdapter,
        api_key=config.openai.api_key,
        chat_model=config.openai.chat_model,
        embedding_model=config.openai.embedding_model
    )
    
    # Repositories (Memory implementations for development)
    document_repository = providers.Factory(MemoryDocumentRepository)
    topic_repository = providers.Factory(MemoryTopicRepository)
    chat_repository = providers.Factory(MemoryChatRepository)
    file_repository = providers.Factory(MemoryDocumentRepository)  # Placeholder
    
    # Document Use Cases
    create_document_use_case = providers.Factory(
        CreateDocumentUseCase,
        document_repository=document_repository,
        processing_service=ai_service,
        vector_search_service=ai_service
    )
    
    get_document_use_case = providers.Factory(
        GetDocumentUseCase,
        document_repository=document_repository
    )
    
    search_documents_use_case = providers.Factory(
        SearchDocumentsUseCase,
        document_repository=document_repository,
        vector_search_service=ai_service
    )
    
    process_file_use_case = providers.Factory(
        ProcessFileUseCase,
        file_repository=file_repository,
        document_repository=document_repository,
        processing_service=ai_service,
        vector_search_service=ai_service
    )
    
    # Chat Use Cases
    start_chat_session_use_case = providers.Factory(
        StartChatSessionUseCase,
        chat_repository=chat_repository,
        topic_repository=topic_repository
    )
    
    send_message_use_case = providers.Factory(
        SendMessageUseCase,
        chat_repository=chat_repository,
        document_repository=document_repository,
        chat_service=ai_service,
        vector_search_service=ai_service
    )
    
    # Knowledge Use Cases
    create_topic_use_case = providers.Factory(
        CreateTopicUseCase,
        topic_repository=topic_repository
    )
    
    get_topic_use_case = providers.Factory(
        GetTopicUseCase,
        topic_repository=topic_repository
    )


class DevelopmentContainer(Container):
    """Container configured for development environment."""
    
    # Override repositories with memory implementations
    document_repository = providers.Singleton(MemoryDocumentRepository)
    topic_repository = providers.Singleton(MemoryTopicRepository)
    chat_repository = providers.Singleton(MemoryChatRepository)


class ProductionContainer(Container):
    """Container configured for production environment."""
    
    # Would use SQLAlchemy implementations
    # document_repository = providers.Factory(
    #     SqlAlchemyDocumentRepository,
    #     session=database_session
    # )
    pass


def create_container(environment: str = "development", config: Optional[Dict[str, Any]] = None) -> Container:
    """Create and configure a container for the specified environment."""
    
    if environment == "development":
        container = DevelopmentContainer()
    elif environment == "production":
        container = ProductionContainer()
    else:
        container = Container()
    
    # Configure with provided config
    if config:
        container.config.from_dict(config)
    
    return container