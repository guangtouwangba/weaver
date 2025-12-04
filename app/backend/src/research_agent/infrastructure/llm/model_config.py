"""Model configuration for context window sizes and capabilities."""

# Model context window sizes (in tokens)
MODEL_CONTEXT_WINDOWS = {
    "openai/gpt-4o-mini": 128_000,
    "openai/gpt-4o": 128_000,
    "openai/gpt-4-turbo": 128_000,
    "anthropic/claude-3.5-haiku": 200_000,
    "anthropic/claude-3.5-sonnet": 200_000,
    "anthropic/claude-3-opus": 200_000,
    "google/gemini-1.5-pro": 2_000_000,
    "google/gemini-1.5-flash": 1_000_000,
    "google/gemini-2.0-flash-exp": 1_000_000,
    "meta-llama/llama-3.2-3b-instruct": 128_000,
    "default": 128_000,  # Default fallback
}


def get_model_context_window(model: str) -> int:
    """
    Get context window size for a model.
    
    Args:
        model: Model identifier (e.g., "openai/gpt-4o-mini")
    
    Returns:
        Context window size in tokens
    """
    # Try exact match first
    if model in MODEL_CONTEXT_WINDOWS:
        return MODEL_CONTEXT_WINDOWS[model]
    
    # Try partial match (e.g., "gpt-4o-mini" matches "openai/gpt-4o-mini")
    for key, value in MODEL_CONTEXT_WINDOWS.items():
        if model in key or key.split("/")[-1] in model:
            return value
    
    # Fallback to default
    return MODEL_CONTEXT_WINDOWS["default"]


def calculate_available_tokens(model: str, safety_ratio: float = 0.55) -> int:
    """
    Calculate available tokens for long context mode.
    
    Args:
        model: Model identifier
        safety_ratio: Safety ratio (default 0.55 = 55% of context window)
    
    Returns:
        Available tokens for long context
    """
    context_window = get_model_context_window(model)
    return int(context_window * safety_ratio)


