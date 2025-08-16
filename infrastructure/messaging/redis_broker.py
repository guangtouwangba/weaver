"""
Redis-based message broker implementation.

Provides Redis Pub/Sub and Redis Streams based messaging capabilities
with support for event buses, task queues, and message persistence.
"""

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, RedisError

from .interfaces import (
    IMessageBroker, IEventBus, ITaskQueue, IMessageStore,
    Message, MessageHandler, MessagePriority, MessageStatus,
    SubscriptionConfig, SystemEvents, SystemTasks
)

logger = logging.getLogger(__name__)


class RedisMessageBroker(IMessageBroker, IEventBus, ITaskQueue, IMessageStore):
    """
    Redis-based implementation of messaging interfaces.
    
    Uses Redis Pub/Sub for event bus functionality and Redis Streams
    for reliable task queue and message store operations.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        database: int = 0,
        max_connections: int = 10,
        message_ttl: timedelta = timedelta(hours=24),
        dead_letter_ttl: timedelta = timedelta(days=7)
    ):
        self.redis_url = redis_url
        self.database = database
        self.max_connections = max_connections
        self.message_ttl = message_ttl
        self.dead_letter_ttl = dead_letter_ttl
        
        self._redis: Optional[Redis] = None
        self._pubsub_redis: Optional[Redis] = None
        self._subscribers: Dict[str, asyncio.Task] = {}
        self._worker_tasks: Dict[str, asyncio.Task] = {}
        self._is_connected = False
        
        # Redis key patterns
        self._message_key = "msg:{message_id}"
        self._topic_stream = "topic:{topic}"
        self._task_queue = "queue:{task_name}"
        self._consumer_group = "group:{topic}:{group}"
        self._dead_letter_queue = "dlq:{topic}"
    
    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            # Main Redis connection for streams and data operations
            self._redis = redis.from_url(
                self.redis_url,
                db=self.database,
                max_connections=self.max_connections,
                encoding='utf-8',
                decode_responses=True
            )
            
            # Separate connection for pub/sub to avoid blocking
            self._pubsub_redis = redis.from_url(
                self.redis_url,
                db=self.database,
                max_connections=self.max_connections,
                encoding='utf-8',
                decode_responses=True
            )
            
            # Test connections
            await self._redis.ping()
            await self._pubsub_redis.ping()
            
            self._is_connected = True
            logger.info("Connected to Redis message broker")
            
        except ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connections to Redis."""
        try:
            # Cancel all subscriber tasks
            for task in self._subscribers.values():
                task.cancel()
            
            # Cancel all worker tasks
            for task in self._worker_tasks.values():
                task.cancel()
            
            # Wait for tasks to complete
            if self._subscribers:
                await asyncio.gather(*self._subscribers.values(), return_exceptions=True)
            if self._worker_tasks:
                await asyncio.gather(*self._worker_tasks.values(), return_exceptions=True)
            
            # Close Redis connections
            if self._redis:
                await self._redis.close()
            if self._pubsub_redis:
                await self._pubsub_redis.close()
            
            self._is_connected = False
            logger.info("Disconnected from Redis message broker")
            
        except Exception as e:
            logger.error(f"Error during Redis disconnect: {e}")
    
    @asynccontextmanager
    async def _ensure_connected(self):
        """Context manager to ensure Redis connection."""
        if not self._is_connected:
            await self.connect()
        try:
            yield
        except ConnectionError:
            # Attempt to reconnect on connection error
            logger.warning("Redis connection lost, attempting to reconnect...")
            await self.connect()
            yield
    
    # IMessageBroker implementation
    
    async def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl: Optional[timedelta] = None
    ) -> str:
        """Publish a message to a Redis stream."""
        async with self._ensure_connected():
            message = Message(
                topic=topic,
                payload=payload,
                headers=headers or {},
                priority=priority,
                expires_at=datetime.utcnow() + (ttl or self.message_ttl)
            )
            
            # Store message
            await self.store_message(message)
            
            # Add to Redis stream
            stream_key = self._topic_stream.format(topic=topic)
            stream_data = {
                'message_id': message.id,
                'payload': json.dumps(payload),
                'headers': json.dumps(headers or {}),
                'priority': priority.value,
                'created_at': message.created_at.isoformat()
            }
            
            await self._redis.xadd(stream_key, stream_data)
            
            # Also publish to pub/sub for real-time subscribers
            pubsub_data = {
                'message_id': message.id,
                'topic': topic,
                'payload': payload,
                'headers': headers or {}
            }
            await self._pubsub_redis.publish(topic, json.dumps(pubsub_data))
            
            logger.debug(f"Published message {message.id} to topic {topic}")
            return message.id
    
    async def subscribe(
        self,
        config: SubscriptionConfig,
        handler: MessageHandler
    ) -> str:
        """Subscribe to a topic using Redis streams."""
        async with self._ensure_connected():
            subscription_id = f"{config.topic}_{id(handler)}"
            
            # Create consumer group if it doesn't exist
            stream_key = self._topic_stream.format(topic=config.topic)
            group_name = config.consumer_group or f"default_{config.topic}"
            
            try:
                await self._redis.xgroup_create(
                    stream_key, group_name, id='0', mkstream=True
                )
            except redis.RedisError:
                # Group might already exist
                pass
            
            # Start consumer task
            task = asyncio.create_task(
                self._consume_stream(config, handler, subscription_id)
            )
            self._subscribers[subscription_id] = task
            
            logger.info(f"Subscribed to topic {config.topic} with ID {subscription_id}")
            return subscription_id
    
    async def _consume_stream(
        self,
        config: SubscriptionConfig,
        handler: MessageHandler,
        subscription_id: str
    ) -> None:
        """Consume messages from a Redis stream."""
        stream_key = self._topic_stream.format(topic=config.topic)
        group_name = config.consumer_group or f"default_{config.topic}"
        consumer_name = f"consumer_{subscription_id}"
        
        semaphore = asyncio.Semaphore(config.max_concurrent)
        
        while True:
            try:
                # Read messages from stream
                messages = await self._redis.xreadgroup(
                    group_name,
                    consumer_name,
                    {stream_key: '>'},
                    count=10,
                    block=1000
                )
                
                for stream, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        async with semaphore:
                            await self._process_stream_message(
                                message_id, fields, config, handler
                            )
                            
            except asyncio.CancelledError:
                logger.info(f"Stream consumer {subscription_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in stream consumer {subscription_id}: {e}")
                await asyncio.sleep(config.retry_delay.total_seconds())
    
    async def _process_stream_message(
        self,
        stream_message_id: str,
        fields: Dict[str, str],
        config: SubscriptionConfig,
        handler: MessageHandler
    ) -> None:
        """Process a single message from Redis stream."""
        try:
            # Reconstruct message object
            message_id = fields.get('message_id')
            if not message_id:
                logger.error(f"No message_id in stream message {stream_message_id}")
                return
            
            # Get full message from store
            message = await self.get_message(message_id)
            if not message:
                logger.error(f"Message {message_id} not found in store")
                return
            
            # Check if message is expired
            if message.is_expired():
                logger.warning(f"Message {message_id} has expired")
                await self.ack_message(message_id)
                return
            
            # Update status to processing
            await self.update_message_status(message_id, MessageStatus.PROCESSING)
            
            # Handle message
            success = await handler.handle(message)
            
            if success:
                await self.update_message_status(message_id, MessageStatus.COMPLETED)
                if config.auto_ack:
                    await self.ack_message(message_id)
            else:
                await self._handle_message_failure(message, config, None)
                
        except Exception as e:
            logger.error(f"Error processing message {stream_message_id}: {e}")
            await self._handle_message_failure(
                await self.get_message(fields.get('message_id', '')),
                config,
                e
            )
    
    async def _handle_message_failure(
        self,
        message: Optional[Message],
        config: SubscriptionConfig,
        error: Optional[Exception]
    ) -> None:
        """Handle message processing failure."""
        if not message:
            return
        
        # Try handler error callback
        if hasattr(self, '_current_handler'):
            should_retry = await self._current_handler.on_error(message, error or Exception("Unknown error"))
        else:
            should_retry = message.can_retry()
        
        if should_retry and message.can_retry():
            message.retry_count += 1
            message.status = MessageStatus.RETRYING
            await self.update_message_status(
                message.id, 
                MessageStatus.RETRYING,
                str(error) if error else None
            )
            
            # Re-queue with delay
            await asyncio.sleep(config.retry_delay.total_seconds())
            await self.publish(
                message.topic,
                message.payload,
                message.headers,
                message.priority
            )
        else:
            # Send to dead letter queue
            await self.update_message_status(
                message.id,
                MessageStatus.DEAD_LETTER,
                str(error) if error else None
            )
            
            if config.dead_letter_topic:
                await self._send_to_dead_letter_queue(message, config.dead_letter_topic)
    
    async def _send_to_dead_letter_queue(self, message: Message, dlq_topic: str) -> None:
        """Send message to dead letter queue."""
        dlq_key = self._dead_letter_queue.format(topic=dlq_topic)
        dlq_data = {
            'original_message_id': message.id,
            'original_topic': message.topic,
            'payload': json.dumps(message.payload),
            'error_message': message.error_message or 'Processing failed',
            'retry_count': message.retry_count,
            'failed_at': datetime.utcnow().isoformat()
        }
        
        await self._redis.xadd(dlq_key, dlq_data)
        
        # Set TTL on dead letter queue
        await self._redis.expire(dlq_key, int(self.dead_letter_ttl.total_seconds()))
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from a topic."""
        if subscription_id in self._subscribers:
            task = self._subscribers.pop(subscription_id)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.info(f"Unsubscribed from {subscription_id}")
            return True
        return False
    
    async def ack_message(self, message_id: str) -> bool:
        """Acknowledge a message (implement based on your needs)."""
        # In Redis streams, acknowledgment happens at the stream level
        # This could be extended to handle specific acknowledgment logic
        return True
    
    async def nack_message(self, message_id: str, requeue: bool = True) -> bool:
        """Negative acknowledge a message."""
        if requeue:
            message = await self.get_message(message_id)
            if message and message.can_retry():
                message.retry_count += 1
                await self.publish(
                    message.topic,
                    message.payload,
                    message.headers,
                    message.priority
                )
        return True
    
    # IEventBus implementation
    
    async def publish_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        source: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Publish an event to the event bus."""
        headers = metadata or {}
        headers['event_type'] = event_type
        headers['source'] = source
        
        return await self.publish(
            topic=f"events.{event_type}",
            payload=event_data,
            headers=headers
        )
    
    async def subscribe_to_events(
        self,
        event_types: List[str],
        handler: Callable[[str, Dict[str, Any]], None],
        consumer_group: Optional[str] = None
    ) -> str:
        """Subscribe to specific event types."""
        
        class EventMessageHandler(MessageHandler):
            async def handle(self, message: Message) -> bool:
                event_type = message.headers.get('event_type', '')
                if event_type in event_types:
                    try:
                        await handler(event_type, message.payload)
                        return True
                    except Exception as e:
                        logger.error(f"Event handler failed: {e}")
                        return False
                return True  # Skip events we're not interested in
        
        # Subscribe to all event topics
        subscription_ids = []
        for event_type in event_types:
            config = SubscriptionConfig(
                topic=f"events.{event_type}",
                consumer_group=consumer_group
            )
            sub_id = await self.subscribe(config, EventMessageHandler())
            subscription_ids.append(sub_id)
        
        return ",".join(subscription_ids)
    
    # ITaskQueue implementation
    
    async def enqueue_task(
        self,
        task_name: str,
        task_args: Dict[str, Any],
        delay: Optional[timedelta] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        max_retries: int = 3
    ) -> str:
        """Enqueue a task for background processing."""
        
        # Add delay if specified
        if delay:
            await asyncio.sleep(delay.total_seconds())
        
        message = Message(
            topic=f"tasks.{task_name}",
            payload=task_args,
            headers={'task_name': task_name},
            priority=priority,
            max_retries=max_retries
        )
        
        return await self.publish(
            topic=f"tasks.{task_name}",
            payload=task_args,
            headers={'task_name': task_name},
            priority=priority
        )
    
    async def register_worker(
        self,
        task_name: str,
        worker_function: Callable[[Dict[str, Any]], Any],
        concurrency: int = 1
    ) -> str:
        """Register a worker function for a task type."""
        
        class TaskMessageHandler(MessageHandler):
            async def handle(self, message: Message) -> bool:
                try:
                    result = await worker_function(message.payload)
                    logger.debug(f"Task {task_name} completed: {result}")
                    return True
                except Exception as e:
                    logger.error(f"Task {task_name} failed: {e}")
                    return False
        
        config = SubscriptionConfig(
            topic=f"tasks.{task_name}",
            consumer_group=f"workers.{task_name}",
            max_concurrent=concurrency
        )
        
        worker_id = await self.subscribe(config, TaskMessageHandler())
        self._worker_tasks[task_name] = self._subscribers[worker_id]
        
        logger.info(f"Registered worker for task {task_name} with concurrency {concurrency}")
        return worker_id
    
    async def get_task_status(self, task_id: str) -> Optional[MessageStatus]:
        """Get the status of a task."""
        message = await self.get_message(task_id)
        return message.status if message else None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task (simplified implementation)."""
        # In a full implementation, this would remove from queues
        await self.update_message_status(task_id, MessageStatus.FAILED, "Cancelled")
        return True
    
    # IMessageStore implementation
    
    async def store_message(self, message: Message) -> None:
        """Store a message in Redis."""
        async with self._ensure_connected():
            key = self._message_key.format(message_id=message.id)
            data = {
                'id': message.id,
                'topic': message.topic,
                'payload': json.dumps(message.payload),
                'headers': json.dumps(message.headers),
                'priority': message.priority.value,
                'created_at': message.created_at.isoformat(),
                'expires_at': message.expires_at.isoformat() if message.expires_at else '',
                'retry_count': message.retry_count,
                'max_retries': message.max_retries,
                'status': message.status.value,
                'error_message': message.error_message or ''
            }
            
            await self._redis.hset(key, mapping=data)
            await self._redis.expire(key, int(self.message_ttl.total_seconds()))
    
    async def get_message(self, message_id: str) -> Optional[Message]:
        """Retrieve a message by ID."""
        async with self._ensure_connected():
            key = self._message_key.format(message_id=message_id)
            data = await self._redis.hgetall(key)
            
            if not data:
                return None
            
            return Message(
                id=data['id'],
                topic=data['topic'],
                payload=json.loads(data['payload']),
                headers=json.loads(data['headers']),
                priority=MessagePriority(int(data['priority'])),
                created_at=datetime.fromisoformat(data['created_at']),
                expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None,
                retry_count=int(data['retry_count']),
                max_retries=int(data['max_retries']),
                status=MessageStatus(data['status']),
                error_message=data['error_message'] if data['error_message'] else None
            )
    
    async def update_message_status(
        self,
        message_id: str,
        status: MessageStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update message status."""
        async with self._ensure_connected():
            key = self._message_key.format(message_id=message_id)
            updates = {'status': status.value}
            if error_message:
                updates['error_message'] = error_message
            
            await self._redis.hset(key, mapping=updates)
    
    async def get_pending_messages(
        self,
        topic: str,
        limit: int = 100
    ) -> List[Message]:
        """Get pending messages for a topic (simplified implementation)."""
        # This would be implemented using Redis streams XPENDING
        # For now, return empty list
        return []
    
    async def cleanup_expired_messages(self) -> int:
        """Clean up expired messages."""
        # This would scan for expired message keys and delete them
        # Simplified implementation
        return 0
    
    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            if not self._is_connected:
                return False
            await self._redis.ping()
            return True
        except Exception:
            return False