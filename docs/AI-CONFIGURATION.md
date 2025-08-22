# AI Model Provider Configuration Guide

This guide explains how to configure different AI model providers for the RAG Knowledge Management System.

## Quick Start

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your AI provider configuration:
   ```bash
   # For OpenAI
   AI__EMBEDDING__OPENAI__API_KEY=your-openai-api-key
   AI__CHAT__OPENAI__API_KEY=your-openai-api-key
   
   # For Anthropic  
   AI__CHAT__ANTHROPIC__API_KEY=your-anthropic-api-key
   ```

## Supported Providers

### OpenAI (Recommended)
Best for production use with high-quality embeddings and chat.

```bash
# Enable OpenAI providers
AI__EMBEDDING__PROVIDER=openai
AI__CHAT__PROVIDER=openai

# OpenAI API Configuration
AI__EMBEDDING__OPENAI__API_KEY=sk-your-api-key
AI__CHAT__OPENAI__API_KEY=sk-your-api-key

# Optional: Custom models
AI__EMBEDDING__OPENAI__EMBEDDING_MODEL=text-embedding-ada-002
AI__CHAT__OPENAI__CHAT_MODEL=gpt-3.5-turbo
```

### Anthropic Claude
Excellent for chat interactions with longer context windows.

```bash
# Enable Anthropic for chat
AI__CHAT__PROVIDER=anthropic

# Anthropic API Configuration
AI__CHAT__ANTHROPIC__API_KEY=sk-ant-your-api-key

# Optional: Specify model
AI__CHAT__ANTHROPIC__CHAT_MODEL=claude-3-sonnet-20240229
```

### HuggingFace
Free option for testing and development.

```bash
# Enable HuggingFace providers
AI__EMBEDDING__PROVIDER=huggingface
AI__CHAT__PROVIDER=huggingface

# Optional: HuggingFace API key for private models
AI__EMBEDDING__HUGGINGFACE__API_KEY=hf_your-token
AI__CHAT__HUGGINGFACE__API_KEY=hf_your-token

# Optional: Custom models
AI__EMBEDDING__HUGGINGFACE__EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
AI__CHAT__HUGGINGFACE__CHAT_MODEL=microsoft/DialoGPT-medium
```

### Local LLM (Ollama)
Run models locally for privacy and cost efficiency.

```bash
# Enable local providers
AI__EMBEDDING__PROVIDER=local
AI__CHAT__PROVIDER=local

# Local API endpoints
AI__EMBEDDING__LOCAL__API_BASE=http://localhost:11434
AI__CHAT__LOCAL__API_BASE=http://localhost:11434

# Local models (must be installed in Ollama)
AI__EMBEDDING__LOCAL__EMBEDDING_MODEL=nomic-embed-text
AI__CHAT__LOCAL__CHAT_MODEL=llama2
```

## Mixed Provider Setup

You can use different providers for different services:

```bash
# Use OpenAI for embeddings (high quality)
AI__EMBEDDING__PROVIDER=openai
AI__EMBEDDING__OPENAI__API_KEY=sk-your-openai-key

# Use Anthropic for chat (better reasoning)
AI__CHAT__PROVIDER=anthropic
AI__CHAT__ANTHROPIC__API_KEY=sk-ant-your-anthropic-key
```

## Advanced Configuration

### Rate Limiting
```bash
AI__RATE_LIMIT_REQUESTS_PER_MINUTE=60
AI__RATE_LIMIT_TOKENS_PER_MINUTE=100000
```

### Caching
```bash
AI__ENABLE_CACHING=true
AI__CACHE_TTL=3600
```

### Embedding Settings
```bash
AI__EMBEDDING__CHUNK_SIZE=1000
AI__EMBEDDING__OVERLAP=200
AI__EMBEDDING__BATCH_SIZE=100
```

### Request Timeouts
```bash
AI__EMBEDDING__OPENAI__TIMEOUT=60
AI__CHAT__OPENAI__TIMEOUT=120
AI__CHAT__ANTHROPIC__TIMEOUT=120
```

## Troubleshooting

### Common Issues

1. **"OpenAI初始化失败: The api_key client option must be set"**
   - Set your OpenAI API key: `AI__EMBEDDING__OPENAI__API_KEY=sk-your-key`
   - Ensure the API key is valid and has sufficient credits

2. **"Anthropic initialization failed"**
   - Set your Anthropic API key: `AI__CHAT__ANTHROPIC__API_KEY=sk-ant-your-key`
   - Check API key permissions and billing status

3. **"HuggingFace model loading failed"**
   - Some models require authentication
   - Set `AI__EMBEDDING__HUGGINGFACE__API_KEY=hf_your-token`

4. **"Local LLM connection refused"**
   - Ensure Ollama is running: `ollama serve`
   - Check the API endpoint: `AI__EMBEDDING__LOCAL__API_BASE=http://localhost:11434`
   - Install required models: `ollama pull llama2`

### Testing Configuration

Test your configuration:

```bash
python -c "
from config.settings import AppConfig
config = AppConfig()
print(f'Embedding provider: {config.ai.embedding.provider}')
print(f'Chat provider: {config.ai.chat.provider}')
print(f'OpenAI key configured: {bool(config.ai.embedding.openai.api_key)}')
"
```

## Best Practices

1. **Security**: Never commit API keys to version control
2. **Cost**: Start with smaller models for development
3. **Fallback**: Enable fallback providers for reliability
4. **Monitoring**: Monitor API usage and costs
5. **Local Development**: Use HuggingFace or local models for development

## Getting API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/
- **HuggingFace**: https://huggingface.co/settings/tokens

## Support

For additional help:
1. Check the application logs for detailed error messages
2. Verify your API keys are valid and have sufficient credits
3. Test with simple models first before using advanced ones