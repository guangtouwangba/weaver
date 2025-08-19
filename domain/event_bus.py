

class DomainEventBus:
    """
    DomainEventBus is an interface for a domain event bus.
    It allows for publishing and subscribing to domain events.
    """

    def publish(self, event):
        """
        Publish a domain event.

        :param event: The domain event to publish.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")

    def subscribe(self, handler):
        """
        Subscribe to a domain event handler.

        :param handler: The handler to subscribe to.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")