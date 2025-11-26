"""OpenRouter embedding service implementation."""

from typing import List

from openai import AsyncOpenAI

from research_agent.infrastructure.embedding.base import EmbeddingService


class OpenRouterEmbeddingService(EmbeddingService):
    """OpenRouter embedding service via OpenAI SDK."""

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/text-embedding-3-small",
    ):
        self._model = model
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.OPENROUTER_BASE_URL,
        )

    async def embed(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        if not texts:
            return []

        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in response.data]

