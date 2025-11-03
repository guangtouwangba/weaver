"""LLM helpers and factory functions."""

from typing import Any

from langchain_community.llms import FakeListLLM
from langchain_core.language_models.llms import LLM
from langchain_core.pydantic_v1 import Field, SecretStr
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from shared_config.settings import AppSettings


class OpenRouterLLM(LLM):
    """OpenRouter LLM using OpenAI-compatible API.

    Supports any chat model available on OpenRouter, including:
    - OpenAI: openai/gpt-4, openai/gpt-3.5-turbo
    - Anthropic: anthropic/claude-3-opus, anthropic/claude-3-sonnet
    - Google: google/gemini-pro
    - Meta: meta-llama/llama-3-70b-instruct
    - And many more...

    Example::

        llm = OpenRouterLLM(
            model="openai/gpt-3.5-turbo",
            openrouter_api_key="your-key",
            temperature=0.7,
            max_tokens=500,
        )
        response = llm("Tell me a joke")

    Note:
        Replace "your-key" with your actual OpenRouter API key from
        https://openrouter.ai/keys
    """

    client: Any = Field(default=None, exclude=True)  #: :meta private:
    model: str = Field(default="openai/gpt-3.5-turbo")
    openrouter_api_key: str | None = Field(default=None)
    base_url: str = Field(default="https://openrouter.ai/api/v1")

    # Optional headers for OpenRouter rankings
    site_url: str | None = Field(default=None)
    site_name: str | None = Field(default=None)

    # Generation parameters
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=500, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    n: int = Field(default=1, ge=1)
    stop: str | None = Field(default=None)

    # Request parameters
    max_retries: int = Field(default=3)
    timeout: float | None = Field(default=60.0)

    # Track token usage (use dict to avoid Pydantic v1 private field issues)
    token_usage: dict[str, int] = Field(default_factory=lambda: {"total": 0, "prompt": 0, "completion": 0}, exclude=True)

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True

    def __init__(self, **data: Any):
        """Initialize OpenRouter LLM."""
        super().__init__(**data)

        # Initialize OpenAI client with OpenRouter endpoint
        self.client = OpenAI(
            api_key=self.openrouter_api_key if self.openrouter_api_key else None,
            base_url=self.base_url,
            max_retries=self.max_retries,
            timeout=self.timeout,
        )

    def _get_extra_headers(self) -> dict[str, str]:
        """Build extra headers for OpenRouter."""
        headers = {}
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name
        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _call_with_retry(self, prompt: str, stop: list[str] | None = None) -> str:
        """Call OpenRouter API with retry logic.

        Args:
            prompt: The prompt to send to the model.
            stop: Optional list of stop sequences.

        Returns:
            The generated text response.
        """
        # Build request parameters
        params: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "n": self.n,
        }

        if stop or self.stop:
            params["stop"] = stop if stop else [self.stop]

        # Add extra headers if provided
        extra_headers = self._get_extra_headers()

        # Log API call details
        print(f"  📡 调用 OpenRouter LLM API...")
        print(f"    ├─ Endpoint: {self.base_url}")
        print(f"    ├─ Model: {self.model}")
        print(f"    ├─ Temperature: {self.temperature}")
        print(f"    ├─ Max Tokens: {self.max_tokens}")

        # Call OpenRouter API
        print(f"    └─ 发送请求...")
        response = self.client.chat.completions.create(
            extra_headers=extra_headers if extra_headers else None, **params
        )
        print(f"    ✓ API 响应成功")

        # Track token usage
        if hasattr(response, "usage") and response.usage:
            self.token_usage["prompt"] += response.usage.prompt_tokens
            self.token_usage["completion"] += response.usage.completion_tokens
            self.token_usage["total"] += response.usage.total_tokens
            print(f"    ✓ Token 使用: Prompt={response.usage.prompt_tokens}, "
                  f"Completion={response.usage.completion_tokens}, "
                  f"Total={response.usage.total_tokens}")

        # Extract the generated text
        return response.choices[0].message.content

    def _call(self, prompt: str, stop: list[str] | None = None, **kwargs: Any) -> str:
        """Call the OpenRouter API.

        Args:
            prompt: The prompt to send to the model.
            stop: Optional list of stop sequences.
            **kwargs: Additional keyword arguments (ignored).

        Returns:
            The generated text response.
        """
        return self._call_with_retry(prompt, stop)

    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "openrouter"

    def get_token_usage(self) -> dict[str, int]:
        """Get cumulative token usage statistics.

        Returns:
            Dictionary with prompt_tokens, completion_tokens, and total_tokens.
        """
        return {
            "prompt_tokens": self.token_usage["prompt"],
            "completion_tokens": self.token_usage["completion"],
            "total_tokens": self.token_usage["total"],
        }

    def reset_token_usage(self) -> None:
        """Reset token usage counters."""
        self.token_usage["prompt"] = 0
        self.token_usage["completion"] = 0
        self.token_usage["total"] = 0


def build_llm(settings: AppSettings) -> LLM:
    """Return an LLM implementation based on configured provider.

    Supported providers:
    - openrouter: OpenRouter LLM (supports multiple models)
    - openai: OpenAI LLM (using OpenRouterLLM with openai_api_key)
    - fake: Fake LLM for testing

    Args:
        settings: Application settings containing LLM configuration.

    Returns:
        LLM instance based on the configured provider.
    """
    provider = settings.llm.provider.lower()

    if provider == "openrouter":
        # Extract API key from SecretStr if present
        api_key = (
            settings.llm.openrouter_api_key.get_secret_value()
            if settings.llm.openrouter_api_key
            else None
        )
        return OpenRouterLLM(
            model=settings.llm.model,
            openrouter_api_key=api_key,
            site_url=settings.llm.openrouter_site_url,
            site_name=settings.llm.openrouter_site_name,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            top_p=settings.llm.top_p,
            frequency_penalty=settings.llm.frequency_penalty,
            presence_penalty=settings.llm.presence_penalty,
            n=settings.llm.n,
            stop=settings.llm.stop,
            max_retries=settings.llm.max_retries,
            timeout=settings.llm.timeout,
        )

    elif provider == "openai":
        # Use OpenRouterLLM with OpenAI credentials
        # Can switch to native OpenAI later if needed
        api_key = (
            settings.llm.openai_api_key.get_secret_value()
            if settings.llm.openai_api_key
            else None
        )
        return OpenRouterLLM(
            model=settings.llm.model,
            openrouter_api_key=api_key,
            base_url=settings.llm.openai_base_url or "https://api.openai.com/v1",
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            top_p=settings.llm.top_p,
            frequency_penalty=settings.llm.frequency_penalty,
            presence_penalty=settings.llm.presence_penalty,
            n=settings.llm.n,
            stop=settings.llm.stop,
            max_retries=settings.llm.max_retries,
            timeout=settings.llm.timeout,
        )

    # Default to fake LLM for development
    return FakeListLLM(responses=["This is a placeholder answer from FakeLLM."])

