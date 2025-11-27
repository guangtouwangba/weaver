"""LangChain wrapper for OpenRouter LLM service."""

from typing import Optional

from langchain_openai import ChatOpenAI


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


# Recommended models by tier
OPENROUTER_MODELS = {
    "cheap": "meta-llama/llama-3.2-3b-instruct:free",
    "fast": "google/gemini-flash-1.5-8b",
    "balanced": "anthropic/claude-3.5-haiku",
    "default": "openai/gpt-4o-mini",
    "quality": "anthropic/claude-3.5-sonnet",
    "best": "openai/gpt-4o",
}

