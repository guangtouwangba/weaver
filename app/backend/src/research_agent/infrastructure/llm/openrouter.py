"""OpenRouter LLM service implementation."""

from typing import AsyncIterator, List, Optional

from openai import AsyncOpenAI

from research_agent.infrastructure.llm.base import ChatMessage, ChatResponse, LLMService

# OpenRouter recommended models by tier
OPENROUTER_MODELS = {
    "cheap": "meta-llama/llama-3.2-3b-instruct:free",
    "fast": "google/gemini-flash-1.5-8b",
    "balanced": "anthropic/claude-3.5-haiku",
    "default": "openai/gpt-4o-mini",
    "quality": "anthropic/claude-3.5-sonnet",
    "best": "openai/gpt-4o",
}


class OpenRouterLLMService(LLMService):
    """OpenRouter LLM service - unified access to 400+ models."""

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        site_url: Optional[str] = None,
        site_name: Optional[str] = None,
    ):
        self._api_key = api_key
        self._model = model
        self._site_url = site_url
        self._site_name = site_name

        # Use OpenAI SDK with OpenRouter base URL
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.OPENROUTER_BASE_URL,
            default_headers=self._get_headers(),
        )

    def _get_headers(self) -> dict:
        """Get OpenRouter recommended headers."""
        headers = {}
        if self._site_url:
            headers["HTTP-Referer"] = self._site_url
        if self._site_name:
            headers["X-Title"] = self._site_name
        return headers

    async def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        """Send chat messages and get response."""
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )

        return ChatResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        )

    async def chat_stream(self, messages: List[ChatMessage]) -> AsyncIterator[str]:
        """Send chat messages and get streaming response."""
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def with_model(self, model: str) -> "OpenRouterLLMService":
        """Create new instance with different model."""
        return OpenRouterLLMService(
            api_key=self._api_key,
            model=model,
            site_url=self._site_url,
            site_name=self._site_name,
        )


def create_llm_service(
    api_key: str,
    tier: str = "default",
) -> OpenRouterLLMService:
    """Factory function to create LLM service by tier."""
    model = OPENROUTER_MODELS.get(tier, OPENROUTER_MODELS["default"])
    return OpenRouterLLMService(
        api_key=api_key,
        model=model,
        site_name="Research Agent RAG",
    )

