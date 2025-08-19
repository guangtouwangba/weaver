from abc import ABC, abstractmethod

from domain.shared.domain_event import DomainEvent


class EventHandler(ABC):
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """处理事件"""
        pass

    @property
    @abstractmethod
    def event_type(self) -> str:
        """处理的事件类型"""
        pass