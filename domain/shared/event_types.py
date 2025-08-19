from enum import Enum
from typing import Type, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from domain.shared.domain_event import DomainEvent


class EventType(Enum):
    """Enumeration of event types for the application."""
    FILE_UPLOADED = "file_uploaded"
    FILE_PROCESSING = "file_processing"
    FILE_PROCESSED = "file_processed"
    FILE_DELETED = "file_deleted"
    FILE_CONFIRMED = "file_confirmed"
    FILE_FAILED = "file_failed"



class EventRegistry:
    """Registry for event types."""
    _event_mappings: Dict[EventType, Type['DomainEvent']] = {}

    @classmethod
    def register(cls, event_type: EventType, event_class: Type['DomainEvent']) -> None:
        """注册事件类型和事件类的映射"""
        cls._event_mappings[event_type] = event_class

    @classmethod
    def get_event_class(cls, event_type: EventType) -> Type['DomainEvent']:
        """根据事件类型获取事件类"""
        return cls._event_mappings.get(event_type)

    @classmethod
    def is_registered(cls, event_type: EventType) -> bool:
        """检查事件类型是否已注册"""
        return event_type in cls._event_mappings

    @classmethod
    def get_all_event_types(cls) -> list[EventType]:
        """获取所有已注册的事件类型"""
        return list(cls._event_mappings.keys())