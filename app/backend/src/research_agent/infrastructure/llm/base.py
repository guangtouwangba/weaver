"""LLM service abstract interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional


@dataclass
class ChatMessage:
    """Chat message data class."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    """Chat response data class."""

    content: str
    model: str
    usage: dict
    cost: Optional[float] = None


class LLMService(ABC):
    """Abstract LLM service interface."""

    @abstractmethod
    async def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        """Send chat messages and get response."""
        pass

    @abstractmethod
    async def chat_stream(self, messages: List[ChatMessage]) -> AsyncIterator[str]:
        """Send chat messages and get streaming response."""
        pass

