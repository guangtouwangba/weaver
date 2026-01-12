import asyncio
import os
import sys

# Add backend source to path
sys.path.append(os.path.join(os.getcwd(), "app/backend/src"))

from research_agent.config import get_settings
from research_agent.infrastructure.embedding.openrouter import (
    OpenRouterEmbeddingService,
)


async def main():
    settings = get_settings()
    print(f"Loaded Settings:")
    print(f"  API Key Set: {'Yes' if settings.openrouter_api_key else 'No'}")
    print(f"  Model: {settings.embedding_model}")

    if not settings.openrouter_api_key:
        print("Error: No OpenRouter API key found.")
        return

    service = OpenRouterEmbeddingService(
        api_key=settings.openrouter_api_key, model=settings.embedding_model
    )

    print(f"\nAttempting to embed 'test' with model '{settings.embedding_model}'...")
    try:
        embedding = await service.embed("test")
        print("Success! Embedding generated.")
        print(f"Dimensions: {len(embedding)}")
    except Exception as e:
        print(f"\nFailure with default model: {e}")

    # Try fallback model if the first one failed
    fallback_model = "openai/text-embedding-ada-002"
    if settings.embedding_model != fallback_model:
        print(f"\nAttempting fallback model '{fallback_model}'...")
        service_fallback = OpenRouterEmbeddingService(
            api_key=settings.openrouter_api_key, model=fallback_model
        )
        try:
            embedding = await service_fallback.embed("test")
            print(f"Success with fallback model '{fallback_model}'!")
            print(f"Dimensions: {len(embedding)}")
        except Exception as e:
            print(f"Failure with fallback model: {e}")


if __name__ == "__main__":
    asyncio.run(main())
