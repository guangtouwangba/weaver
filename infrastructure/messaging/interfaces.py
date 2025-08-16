"""
Messaging infrastructure interfaces and abstractions.

This module defines the core interfaces for messaging systems including:
- Event publishing and subscribing
- Task queues for background processing
- Message routing and filtering
- Dead letter queues and error handling
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class MessageStatus(Enum):
    """Message processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


@dataclass
class Message:
    """
    Represents a message in the messaging system.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    status: MessageStatus = MessageStatus.PENDING
    error_message: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return self.retry_count < self.max_retries and self.status == MessageStatus.FAILED


@dataclass
class SubscriptionConfig:
    """Configuration for message subscriptions."""
    topic: str
    consumer_group: Optional[str] = None
    auto_ack: bool = True
    max_concurrent: int = 10
    retry_delay: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    dead_letter_topic: Optional[str] = None


class MessageHandler(ABC):
    """Abstract base class for message handlers."""
    
    @abstractmethod
    async def handle(self, message: Message) -> bool:
        """
        Handle a message.
        
        Args:
            message: The message to process
            
        Returns:
            True if message was handled successfully, False otherwise
        """
        pass
    
    async def on_error(self, message: Message, error: Exception) -> bool:
        """
        Handle processing errors.
        
        Args:
            message: The message that failed
            error: The error that occurred
            
        Returns:
            True if error was handled and message should be retried, False otherwise
        """
        return False


class IMessageBroker(ABC):
    """
    Abstract interface for message brokers.
    
    Defines the core operations that any messaging system must support:
    - Publishing messages
    - Subscribing to topics
    - Message acknowledgment and failure handling
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the message broker."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the message broker."""
        pass
    
    @abstractmethod
    async def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl: Optional[timedelta] = None
    ) -> str:
        """
        Publish a message to a topic.
        
        Args:
            topic: Topic to publish to
            payload: Message payload
            headers: Optional message headers
            priority: Message priority
            ttl: Time to live for the message
            
        Returns:
            Message ID
        """
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        config: SubscriptionConfig,
        handler: MessageHandler
    ) -> str:
        """
        Subscribe to a topic with a message handler.
        
        Args:
            config: Subscription configuration
            handler: Message handler
            
        Returns:
            Subscription ID
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a topic.
        
        Args:
            subscription_id: ID of the subscription to cancel
            
        Returns:
            True if unsubscribed successfully
        """
        pass
    
    @abstractmethod
    async def ack_message(self, message_id: str) -> bool:
        """
        Acknowledge successful processing of a message.
        
        Args:
            message_id: ID of the message to acknowledge
            
        Returns:
            True if acknowledged successfully
        """
        pass
    
    @abstractmethod
    async def nack_message(self, message_id: str, requeue: bool = True) -> bool:
        """
        Negative acknowledge (reject) a message.
        
        Args:
            message_id: ID of the message to reject
            requeue: Whether to requeue the message for retry
            
        Returns:
            True if rejected successfully
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the message broker is healthy."""
        pass


class IEventBus(ABC):
    """
    Abstract interface for event-driven messaging.
    
    Focuses on publish-subscribe patterns for event-driven architecture.
    """
    
    @abstractmethod
    async def publish_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        source: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Publish an event.
        
        Args:
            event_type: Type/name of the event
            event_data: Event payload
            source: Source that generated the event
            metadata: Optional event metadata
            
        Returns:
            Event ID
        """
        pass
    
    @abstractmethod
    async def subscribe_to_events(
        self,
        event_types: List[str],
        handler: Callable[[str, Dict[str, Any]], None],
        consumer_group: Optional[str] = None
    ) -> str:
        """
        Subscribe to specific event types.
        
        Args:
            event_types: List of event types to subscribe to
            handler: Function to handle events
            consumer_group: Optional consumer group for load balancing
            
        Returns:
            Subscription ID
        """
        pass


class ITaskQueue(ABC):
    """
    Abstract interface for task queue systems.
    
    Focuses on background task processing with job scheduling and monitoring.
    """
    
    @abstractmethod
    async def enqueue_task(
        self,
        task_name: str,
        task_args: Dict[str, Any],
        delay: Optional[timedelta] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        max_retries: int = 3
    ) -> str:
        """
        Enqueue a task for background processing.
        
        Args:
            task_name: Name/type of the task
            task_args: Task arguments
            delay: Optional delay before processing
            priority: Task priority
            max_retries: Maximum number of retries
            
        Returns:
            Task ID
        """
        pass
    
    @abstractmethod
    async def register_worker(
        self,
        task_name: str,
        worker_function: Callable[[Dict[str, Any]], Any],
        concurrency: int = 1
    ) -> str:
        """
        Register a worker function for a task type.
        
        Args:
            task_name: Name of the task type to handle
            worker_function: Function to process tasks
            concurrency: Number of concurrent workers
            
        Returns:
            Worker registration ID
        """
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[MessageStatus]:
        """
        Get the status of a task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task status or None if not found
        """
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if cancelled successfully
        """
        pass


class IMessageStore(ABC):
    """
    Abstract interface for message persistence.
    
    Handles message storage, retrieval, and cleanup.
    """
    
    @abstractmethod
    async def store_message(self, message: Message) -> None:
        """Store a message."""
        pass
    
    @abstractmethod
    async def get_message(self, message_id: str) -> Optional[Message]:
        """Retrieve a message by ID."""
        pass
    
    @abstractmethod
    async def update_message_status(
        self,
        message_id: str,
        status: MessageStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update message status."""
        pass
    
    @abstractmethod
    async def get_pending_messages(
        self,
        topic: str,
        limit: int = 100
    ) -> List[Message]:
        """Get pending messages for a topic."""
        pass
    
    @abstractmethod
    async def cleanup_expired_messages(self) -> int:
        """Clean up expired messages and return count removed."""
        pass


# Event types for common system events
class SystemEvents:
    """Common system event types."""
    
    # Document processing events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_PARSING_FAILED = "document.parsing_failed"
    
    # Topic management events
    TOPIC_CREATED = "topic.created"
    TOPIC_UPDATED = "topic.updated"
    TOPIC_DELETED = "topic.deleted"
    
    # User activity events
    USER_SESSION_STARTED = "user.session_started"
    USER_SESSION_ENDED = "user.session_ended"
    
    # System health events
    SYSTEM_HEALTH_CHECK = "system.health_check"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"


# Task types for common background tasks
class SystemTasks:
    """Common system task types."""
    
    # Document processing tasks
    PARSE_DOCUMENT = "parse_document"
    GENERATE_EMBEDDINGS = "generate_embeddings"
    INDEX_DOCUMENT = "index_document"
    
    # Maintenance tasks
    CLEANUP_EXPIRED_SESSIONS = "cleanup_expired_sessions"
    BACKUP_DATABASE = "backup_database"
    HEALTH_CHECK = "health_check"
    
    # Notification tasks
    SEND_EMAIL = "send_email"
    SEND_WEBHOOK = "send_webhook"