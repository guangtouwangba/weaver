"""Test LLM integration with different providers."""

import pytest

from rag_core.chains.llm import OpenRouterLLM, build_llm
from shared_config.settings import AppSettings, LLMConfig


def test_openrouter_llm_initialization():
    """Test OpenRouterLLM can be initialized."""
    llm = OpenRouterLLM(
        model="openai/gpt-3.5-turbo",
        openrouter_api_key="test-key",
        temperature=0.5,
        max_tokens=100,
    )

    assert llm.model == "openai/gpt-3.5-turbo"
    assert llm.temperature == 0.5
    assert llm.max_tokens == 100
    assert llm._llm_type == "openrouter"


def test_openrouter_llm_token_tracking():
    """Test token usage tracking."""
    llm = OpenRouterLLM(
        model="openai/gpt-3.5-turbo",
        openrouter_api_key="test-key",
    )

    # Initially should be zero
    usage = llm.get_token_usage()
    assert usage["prompt_tokens"] == 0
    assert usage["completion_tokens"] == 0
    assert usage["total_tokens"] == 0

    # Reset should work
    llm.reset_token_usage()
    usage = llm.get_token_usage()
    assert usage["total_tokens"] == 0


def test_build_llm_fake_provider(monkeypatch):
    """Test build_llm with fake provider."""
    from langchain_community.llms import FakeListLLM

    # Clear environment variables BEFORE creating config
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_TEMPERATURE", raising=False)
    
    # Set fake provider explicitly
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    # Create config after clearing env vars
    config = LLMConfig()
    settings = AppSettings(llm=config)  # type: ignore[arg-type]

    llm = build_llm(settings)
    assert isinstance(llm, FakeListLLM)


def test_build_llm_openrouter_provider(monkeypatch):
    """Test build_llm with openrouter provider."""
    from pydantic import SecretStr

    # Clear ALL LLM-related environment variables
    for key in ["LLM_PROVIDER", "LLM_MODEL", "LLM_TEMPERATURE", "LLM_MAX_TOKENS",
                "LLM_TOP_P", "LLM_FREQUENCY_PENALTY", "LLM_PRESENCE_PENALTY",
                "LLM_N", "LLM_STOP", "LLM_MAX_RETRIES", "LLM_TIMEOUT",
                "OPENROUTER_API_KEY", "OPENAI_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    
    # Set test values explicitly
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-3.5-turbo")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.8")
    monkeypatch.setenv("LLM_MAX_TOKENS", "300")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    config = LLMConfig()
    settings = AppSettings(llm=config)  # type: ignore[arg-type]
    llm = build_llm(settings)

    assert isinstance(llm, OpenRouterLLM)
    assert llm.model == "openai/gpt-3.5-turbo"
    assert llm.temperature == 0.8
    assert llm.max_tokens == 300


def test_build_llm_respects_all_parameters(monkeypatch):
    """Test that build_llm respects all LLM configuration parameters."""
    from pydantic import SecretStr

    # Clear all environment variables that might interfere
    for key in ["LLM_PROVIDER", "LLM_MODEL", "LLM_TEMPERATURE", "LLM_MAX_TOKENS",
                "LLM_TOP_P", "LLM_FREQUENCY_PENALTY", "LLM_PRESENCE_PENALTY",
                "LLM_N", "LLM_STOP", "LLM_MAX_RETRIES", "LLM_TIMEOUT",
                "OPENROUTER_API_KEY", "OPENROUTER_SITE_URL", "OPENROUTER_SITE_NAME"]:
        monkeypatch.delenv(key, raising=False)
    
    # Set all test values explicitly via environment
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_MODEL", "anthropic/claude-3-sonnet")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.3")
    monkeypatch.setenv("LLM_MAX_TOKENS", "1000")
    monkeypatch.setenv("LLM_TOP_P", "0.9")
    monkeypatch.setenv("LLM_FREQUENCY_PENALTY", "0.5")
    monkeypatch.setenv("LLM_PRESENCE_PENALTY", "0.5")
    monkeypatch.setenv("LLM_N", "2")
    monkeypatch.setenv("LLM_STOP", "END")
    monkeypatch.setenv("LLM_MAX_RETRIES", "5")
    monkeypatch.setenv("LLM_TIMEOUT", "120.0")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_SITE_URL", "https://example.com")
    monkeypatch.setenv("OPENROUTER_SITE_NAME", "Test App")

    config = LLMConfig()
    settings = AppSettings(llm=config)  # type: ignore[arg-type]
    llm = build_llm(settings)

    assert isinstance(llm, OpenRouterLLM)
    assert llm.model == "anthropic/claude-3-sonnet"
    assert llm.temperature == 0.3
    assert llm.max_tokens == 1000
    assert llm.top_p == 0.9
    assert llm.frequency_penalty == 0.5
    assert llm.presence_penalty == 0.5
    assert llm.n == 2
    assert llm.stop == "END"
    assert llm.max_retries == 5
    assert llm.timeout == 120.0
    assert llm.site_url == "https://example.com"
    assert llm.site_name == "Test App"


@pytest.mark.skip(reason="Requires actual API key and makes real API calls")
def test_openrouter_llm_real_call():
    """Test actual OpenRouter API call (requires valid API key).

    To run this test:
    1. Set OPENROUTER_API_KEY environment variable
    2. Run: pytest -v -k test_openrouter_llm_real_call -s
    """
    import os

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    llm = OpenRouterLLM(
        model="openai/gpt-3.5-turbo",
        openrouter_api_key=api_key,
        temperature=0.7,
        max_tokens=100,
    )

    response = llm("Say 'Hello World' and nothing else.")
    print(f"\nResponse: {response}")

    assert response is not None
    assert len(response) > 0
    assert "hello" in response.lower() or "world" in response.lower()

    # Check token usage was tracked
    usage = llm.get_token_usage()
    print(f"Token usage: {usage}")
    assert usage["total_tokens"] > 0

