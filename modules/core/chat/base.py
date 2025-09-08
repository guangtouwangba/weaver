from abc import ABC
from typing import Optional, List
from core.schema.schemas import ChatMessage


class BaseChatEngine(ABC):

    def chat(self, query: str, history: Optional[List[ChatMessage]] = None) -> str:
        pass

    def achat(self, query: str, history: Optional[List[ChatMessage]] = None) -> str:
        pass

    def stream_chat(self, query: str, history: Optional[List[ChatMessage]] = None) -> str:
        pass