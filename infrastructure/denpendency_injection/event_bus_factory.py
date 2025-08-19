import logging
from typing import Optional

import redis.asyncio as aioredis

from application.event.event_bus import EventBus
from application.event.event_handler import EventHandler
from domain.shared.domain_event import DomainEvent
from infrastructure.config import get_config, RedisConfig

logger = logging.getLogger(__name__)


class MockEventBus(EventBus):
    """Mock EventBus 实现，用于开发和测试环境"""

    def __init__(self):
        self.handlers = []

    async def publish(self, event: DomainEvent) -> None:
        """发布事件到所有订阅的处理器"""
        logger.debug(f"Mock EventBus: Publishing event {event.event_type}")

        for handler in self.handlers:
            if hasattr(handler, 'handle') and callable(handler.handle):
                try:
                    await handler.handle(event)
                except Exception as e:
                    logger.warning(f"Event handler failed: {e}")

    def subscribe(self, handler: EventHandler) -> None:
        """订阅事件处理器"""
        self.handlers.append(handler)
        logger.debug(f"Mock EventBus: Subscribed handler {handler.__class__.__name__}")


async def get_redis_client(redis_config: RedisConfig) -> Optional[aioredis.Redis]:
    """
    获取Redis客户端，包含连接测试
    """
    try:
        redis_client = aioredis.from_url(
            redis_config.url,
            password=redis_config.password,
            db=redis_config.database,
            max_connections=redis_config.max_connections,
            encoding='utf-8',
            decode_responses=True,
            socket_timeout=redis_config.socket_timeout,
            socket_connect_timeout=redis_config.socket_connect_timeout
        )
        
        # 测试连接
        await redis_client.ping()
        logger.info("Redis client connected successfully")
        return redis_client
        
    except (aioredis.RedisError, ConnectionError, TimeoutError) as e:
        logger.warning(f"Redis connection failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating Redis client: {e}")
        return None


async def create_event_bus() -> EventBus:
    """
    创建事件总线实例 - 环境和配置驱动
    """
    config = get_config()
    
    # 根据配置选择具体的事件总线实现
    event_bus_type = config.messaging.event_bus_type
    
    if event_bus_type == 'redis':
        redis_client = await get_redis_client(config.messaging.redis)
        
        if redis_client:
            try:
                from infrastructure.messaging.redis_event_bus import RedisEventBus
                logger.info("Using RedisEventBus for message handling")
                return RedisEventBus(redis_client)
            except ImportError as e:
                logger.error(f"Failed to import RedisEventBus: {e}")
    
    # 回退到Mock实现
    logger.info("Using MockEventBus for message handling (fallback)")
    return MockEventBus()
