from application.event.event_bus import EventBus


class RedisEventBus(EventBus):
    """
    Redis Event Bus implementation for publishing and subscribing to events.
    """

    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.subscribers = {}

    async def publish(self, event):
        """Publish an event to Redis."""
        import json
        
        # Serialize event to JSON for Redis
        try:
            event_data = event.to_dict()
            event_json = json.dumps(event_data, default=str)  # default=str handles datetime objects
            await self.redis_client.publish(event.event_type, event_json)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to publish event {event.event_type}: {e}")
            raise

    def subscribe(self, handler):
        """Subscribe an event handler."""
        if handler.event_type not in self.subscribers:
            self.subscribers[handler.event_type] = []
        self.subscribers[handler.event_type].append(handler)





