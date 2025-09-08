"""
Services模块

提供Business logicService layer，负责编排Repository和处理业务规则。
"""

from modules.services.base_service import BaseService
from modules.services.document_service import DocumentService
from modules.services.file_service import FileService
from modules.services.redis_service import RedisService, redis_service
from modules.services.task_monitoring_service import (
    RedisTaskMonitoringService,
    TaskConfigurationService,
    configuration_service,
    monitoring_service,
)
from modules.services.topic_service import TopicService
from modules.services.rag_integrated_chat_service import (
    RAGIntegratedChatService,
    create_rag_integrated_chat_service,
)
# 保留基础聊天服务以备兼容性需要
from modules.services.chat_service import ChatService, get_chat_service
from modules.services.elasticsearch_service import (
    ElasticsearchChatService,
    elasticsearch_chat_service
)
from modules.services.summary_service import SummaryGenerationService

__all__ = [
    "BaseService",
    "TopicService",
    "FileService",
    "DocumentService",
    "RedisService",
    "redis_service",
    "RedisTaskMonitoringService",
    "TaskConfigurationService",
    "monitoring_service",
    "configuration_service",
    # 新的RAG集成聊天服务（推荐使用）
    "RAGIntegratedChatService",
    "create_rag_integrated_chat_service",
    # 基础聊天服务（兼容性保留）
    "ChatService",
    "get_chat_service",
    "ElasticsearchChatService",
    "elasticsearch_chat_service",
    "SummaryGenerationService",
]
