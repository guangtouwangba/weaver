"""OpenRouter LLM service implementation."""

from typing import AsyncIterator, List, Optional

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI

from research_agent.config import get_settings
from research_agent.infrastructure.llm.base import ChatMessage, ChatResponse, LLMService
from research_agent.shared.utils.logger import logger

# OpenRouter recommended models by tier
OPENROUTER_MODELS = {
    "cheap": "meta-llama/llama-3.2-3b-instruct:free",
    "fast": "google/gemini-flash-1.5-8b",
    "balanced": "anthropic/claude-3.5-haiku",
    "default": "openai/gpt-4o-mini",
    "quality": "anthropic/claude-3.5-sonnet",
    "best": "openai/gpt-4o",
}


def create_langchain_llm(
    api_key: str,
    model: str = "openai/gpt-4o-mini",
    temperature: float = 0.0,
    streaming: bool = False,
    site_url: Optional[str] = None,
    site_name: Optional[str] = None,
) -> ChatOpenAI:
    """
    Create a LangChain ChatOpenAI instance configured for OpenRouter.

    Args:
        api_key: OpenRouter API key
        model: Model identifier (e.g., "openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet")
        temperature: Sampling temperature (0.0 = deterministic)
        streaming: Enable streaming responses
        site_url: Optional site URL for OpenRouter headers
        site_name: Optional site name for OpenRouter headers

    Returns:
        Configured ChatOpenAI instance
    """
    default_headers = {}
    if site_url:
        default_headers["HTTP-Referer"] = site_url
    if site_name:
        default_headers["X-Title"] = site_name

    return ChatOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model=model,
        temperature=temperature,
        streaming=streaming,
        default_headers=default_headers,
    )


def _get_langfuse_client():
    """Get Langfuse client for direct tracing (lazy initialization)."""
    settings = get_settings()
    if not settings.langfuse_enabled:
        return None

    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None

    try:
        import os

        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host

        from langfuse import Langfuse

        return Langfuse()
    except ImportError:
        logger.debug("[Langfuse] Not installed, skipping trace")
        return None
    except Exception as e:
        logger.warning(f"[Langfuse] Failed to initialize: {e}")
        return None


class OpenRouterLLMService(LLMService):
    """OpenRouter LLM service - unified access to 400+ models."""

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        site_url: Optional[str] = None,
        site_name: Optional[str] = None,
        trace_name: Optional[str] = None,  # For Langfuse tracing
    ):
        self._api_key = api_key
        self._model = model
        self._site_url = site_url
        self._site_name = site_name
        self._trace_name = trace_name  # e.g., "mindmap", "summary"

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
        """Send chat messages and get response with optional Langfuse tracing."""
        langfuse = _get_langfuse_client()
        generation = None

        # Create Langfuse generation if enabled (new API v3)
        if langfuse and self._trace_name:
            try:
                # Prepare input data for logging
                input_data = [
                    {
                        "role": m.role,
                        "content": m.content[:500] + "..." if len(m.content) > 500 else m.content,
                    }
                    for m in messages
                ]
                # Use new Langfuse API: start_observation with as_type='generation'
                generation = langfuse.start_observation(
                    as_type="generation",
                    name=f"{self._trace_name}-llm-call",
                    model=self._model,
                    input=input_data,
                    metadata={"trace_name": self._trace_name},
                )
            except Exception as e:
                logger.warning(f"[Langfuse] Failed to create generation: {e}")

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
            )

            result = ChatResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            )

            # Log output to Langfuse (new API: update then end)
            if generation:
                try:
                    output_preview = (
                        result.content[:1000] + "..."
                        if len(result.content) > 1000
                        else result.content
                    )
                    generation.update(
                        output=output_preview,
                        usage_details={
                            "input": result.usage.get("prompt_tokens", 0),
                            "output": result.usage.get("completion_tokens", 0),
                        },
                    )
                    generation.end()
                except Exception as e:
                    logger.warning(f"[Langfuse] Failed to log generation: {e}")

            return result

        except Exception as e:
            # Log error to Langfuse
            if generation:
                try:
                    generation.update(
                        status_message=str(e),
                        level="ERROR",
                    )
                    generation.end()
                except Exception:
                    pass
            raise

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
            trace_name=self._trace_name,
        )

    def with_trace(self, trace_name: str) -> "OpenRouterLLMService":
        """Create new instance with Langfuse trace name."""
        return OpenRouterLLMService(
            api_key=self._api_key,
            model=self._model,
            site_url=self._site_url,
            site_name=self._site_name,
            trace_name=trace_name,
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
