from abc import ABC, abstractmethod

from application.event.event_handler import EventHandler
from domain.shared.domain_event import DomainEvent


class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """发布事件"""
        pass

    @abstractmethod
    def subscribe(self, handler: EventHandler) -> None:
        """订阅事件处理器"""
        pass