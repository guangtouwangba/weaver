"""
Application layer for topic management.

This module exports all topic-related classes and functions for the application layer.
"""

from .topic import (
    # DTOs
    CreateTopicRequest,
    UpdateTopicRequest,
    UploadResourceRequest,
    TopicResponse,
    ResourceResponse,
    
    # Services and Controllers
    TopicApplicationService,
    TopicController,
    
    # Factory function
    create_topic_controller
)

__all__ = [
    'CreateTopicRequest',
    'UpdateTopicRequest', 
    'UploadResourceRequest',
    'TopicResponse',
    'ResourceResponse',
    'TopicApplicationService',
    'TopicController',
    'create_topic_controller'
]