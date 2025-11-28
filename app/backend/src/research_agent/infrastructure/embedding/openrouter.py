"""Embedding service implementations."""

from typing import List

import httpx
from openai import AsyncOpenAI

from research_agent.infrastructure.embedding.base import EmbeddingService


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI embedding service (direct, not via OpenRouter)."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
    ):
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key)

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


class OpenRouterEmbeddingService(EmbeddingService):
    """OpenRouter embedding service using direct HTTP calls.
    
    OpenRouter supports embedding models like openai/text-embedding-3-small.
    See: https://openrouter.ai/openai/text-embedding-3-small/api
    
    Uses httpx directly instead of OpenAI SDK for better compatibility.
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/text-embedding-3-small",
    ):
        self._model = model
        self._api_key = api_key

    async def _call_api(self, input_data: str | List[str]) -> dict:
        """Call OpenRouter embeddings API directly."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.OPENROUTER_BASE_URL}/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "input": input_data,
                    "encoding_format": "float",
                },
            )
            response.raise_for_status()
            return response.json()

    async def embed(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        result = await self._call_api(text)
        return result["data"][0]["embedding"]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        if not texts:
            return []

        result = await self._call_api(texts)
        return [item["embedding"] for item in result["data"]]
