from domain.event import DomainEvent


class EmbeddingEvent(DomainEvent):
    """
    Base class for embedding-related domain events.
    """

    def __init__(self, event_type: str):
        super().__init__(event_type)

    @property
    def event_type(self) -> str:
        """事件类型标识"""
        return "embedding_event"

    def _get_event_data(self) -> dict:
        """获取事件特定数据"""
        return {}