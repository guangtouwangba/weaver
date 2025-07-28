# Multi-Provider AI Support

This document describes the multi-provider AI client architecture that supports OpenAI, DeepSeek, and Anthropic Claude models.

## Overview

The system now supports multiple AI providers through a unified interface, allowing you to:
- Use different providers for different agents
- Switch between providers seamlessly
- Mix and match models from different providers
- Configure fallback strategies

## Supported Providers

### 1. OpenAI
- **Models**: gpt-4o, gpt-4o-mini, gpt-4, gpt-3.5-turbo
- **Features**: Chat, completion, embeddings, function calling
- **API Docs**: https://platform.openai.com/docs

### 2. DeepSeek
- **Models**: deepseek-chat, deepseek-reasoner, deepseek-v3, deepseek-r1
- **Features**: Chat, completion, reasoning
- **API Docs**: https://api-docs.deepseek.com/zh-cn/

### 3. Anthropic Claude
- **Models**: claude-3-5-sonnet, claude-3-5-haiku, claude-3-opus, claude-3-sonnet
- **Features**: Chat, completion, vision, function calling
- **API Docs**: https://docs.anthropic.com/

## Architecture

### Core Components

#### 1. BaseAIClient (Abstract Base Class)
```python
class BaseAIClient(ABC):
    def create_chat_completion(self, messages, model, temperature, max_tokens) -> ChatCompletion
    def get_available_models(self) -> List[str]
    def validate_model(self, model: str) -> bool
```

#### 2. Provider-Specific Clients
- `OpenAIClient`: OpenAI API integration
- `DeepSeekClient`: DeepSeek API integration (OpenAI-compatible)
- `AnthropicClient`: Anthropic Claude API integration

#### 3. AIClientFactory
```python
class AIClientFactory:
    @staticmethod
    def create_client(provider: str, api_key: str) -> BaseAIClient
    @staticmethod
    def get_supported_providers() -> List[str]
    @staticmethod
    def get_provider_info(provider: str) -> Dict[str, Any]
```

#### 4. Data Structures
```python
@dataclass
class ChatMessage:
    role: str  # "system", "user", "assistant"
    content: str

@dataclass
class ChatCompletion:
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]]
    finish_reason: Optional[str]
```

## Usage Examples

### 1. Basic Client Creation
```python
from utils.ai_client import AIClientFactory

# Create OpenAI client
openai_client = AIClientFactory.create_client('openai', 'your-openai-key')

# Create DeepSeek client
deepseek_client = AIClientFactory.create_client('deepseek', 'your-deepseek-key')

# Create Anthropic client
anthropic_client = AIClientFactory.create_client('anthropic', 'your-anthropic-key')
```

### 2. Chat Completion
```python
from utils.ai_client import ChatMessage

messages = [
    ChatMessage(role="system", content="You are a helpful assistant."),
    ChatMessage(role="user", content="What is RAG?")
]

response = client.create_chat_completion(
    messages=messages,
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=200
)

print(f"Response: {response.content}")
print(f"Provider: {response.provider}")
print(f"Model: {response.model}")
```

### 3. Orchestrator with Multiple Providers
```python
from agents.orchestrator import ResearchOrchestrator

orchestrator = ResearchOrchestrator(
    openai_api_key="your-openai-key",
    deepseek_api_key="your-deepseek-key",
    anthropic_api_key="your-anthropic-key",
    default_provider="openai",  # or "deepseek" or "anthropic"
    agent_configs={
        "google_engineer": {
            "provider": "openai",
            "model": "gpt-4o"
        },
        "mit_researcher": {
            "provider": "deepseek", 
            "model": "deepseek-chat"
        },
        "industry_expert": {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022"
        }
    }
)
```

### 4. Agent Configuration
```python
# Each agent can use a different provider
google_agent = GoogleEngineerAgent(
    api_key="your-openai-key",
    model="gpt-4o",
    provider="openai"
)

mit_agent = MITResearcherAgent(
    api_key="your-deepseek-key", 
    model="deepseek-chat",
    provider="deepseek"
)

industry_agent = IndustryExpertAgent(
    api_key="your-anthropic-key",
    model="claude-3-5-sonnet-20241022",
    provider="anthropic"
)
```

## Configuration

### Environment Variables
```bash
# Required for OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Required for DeepSeek  
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# Required for Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Model Mapping

#### OpenAI Models
- `gpt-4o` → OpenAI GPT-4o
- `gpt-4o-mini` → OpenAI GPT-4o-mini
- `gpt-4` → OpenAI GPT-4
- `gpt-3.5-turbo` → OpenAI GPT-3.5-turbo

#### DeepSeek Models
- `gpt-4o-mini` → `deepseek-chat` (mapped)
- `gpt-4o` → `deepseek-chat` (mapped)
- `gpt-4` → `deepseek-chat` (mapped)
- `gpt-3.5-turbo` → `deepseek-chat` (mapped)
- `deepseek-chat` → `deepseek-chat` (native)
- `deepseek-reasoner` → `deepseek-reasoner` (native)

#### Anthropic Models
- `claude-3-5-sonnet-20241022` → Anthropic Claude 3.5 Sonnet
- `claude-3-5-haiku-20241022` → Anthropic Claude 3.5 Haiku
- `claude-3-opus-20240229` → Anthropic Claude 3 Opus
- `claude-3-sonnet-20240229` → Anthropic Claude 3 Sonnet

## Advanced Features

### 1. Model Validation
```python
# Check if a model is available for a provider
client = AIClientFactory.create_client('openai', 'your-key')
is_valid = client.validate_model('gpt-4o-mini')  # True
is_valid = client.validate_model('deepseek-chat')  # False
```

### 2. Provider Information
```python
# Get information about a provider
info = AIClientFactory.get_provider_info('deepseek')
print(info['supported_models'])
print(info['features'])
print(info['api_docs_url'])
```

### 3. Available Models
```python
# Get all available models for a client
client = AIClientFactory.create_client('openai', 'your-key')
models = client.get_available_models()
print(models)  # ['gpt-4o', 'gpt-4o-mini', 'gpt-4', ...]
```

## Error Handling

The system includes robust error handling:
- Invalid provider names
- Missing API keys
- Network timeouts
- Model validation errors
- Provider-specific API errors

## Demo Script

Run the demo script to test multi-provider support:

```bash
python demo_multi_provider.py
```

This will:
1. Show provider information
2. Test client creation
3. Demo chat completion
4. Validate models
5. Test orchestrator integration

## Migration from Old System

### Before (Single Provider)
```python
# Old way - OpenAI only
orchestrator = ResearchOrchestrator(
    openai_api_key="your-key"
)
```

### After (Multi-Provider)
```python
# New way - Multiple providers
orchestrator = ResearchOrchestrator(
    openai_api_key="your-openai-key",
    deepseek_api_key="your-deepseek-key", 
    anthropic_api_key="your-anthropic-key",
    default_provider="openai"
)
```

## Benefits

1. **Flexibility**: Use the best model for each task
2. **Cost Optimization**: Choose providers based on pricing
3. **Reliability**: Fallback options if one provider is down
4. **Performance**: Different models excel at different tasks
5. **Future-Proof**: Easy to add new providers

## Future Enhancements

- Support for more providers (Google Gemini, Cohere, etc.)
- Automatic provider selection based on task
- Cost tracking and optimization
- Load balancing between providers
- Advanced fallback strategies 