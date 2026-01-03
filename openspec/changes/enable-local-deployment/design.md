# Design: Enable Local Deployment

## Context

The current implementation is tightly coupled to cloud API services:
1. **LLM Layer**: Uses `ChatOpenAI` from LangChain with hardcoded OpenRouter base URL
2. **Embedding Layer**: Directly uses OpenAI or OpenRouter embedding APIs with 1536-dimension assumption
3. **Database**: Vector columns fixed at 1536 dimensions in PostgreSQL models
4. **Context Management**: Model context windows configured for cloud models only

Users requiring local deployment (privacy, offline, cost) cannot use the system without significant modifications.

## Goals
- Enable full air-gapped operation with local models
- Maintain backward compatibility with OpenRouter/OpenAI
- Minimize code changes through abstraction
- Support multiple local LLM providers (Ollama, vLLM, LocalAI)

## Non-Goals
- Model management/downloading (user responsibility)
- GPU scheduling/resource management
- Model fine-tuning support
- Automatic dimension migration

## Decisions

### Decision 1: OpenAI-Compatible API Strategy

**Choice**: Use OpenAI SDK with configurable base URL for all LLM interactions

**Rationale**:
- Ollama, vLLM, LocalAI all expose OpenAI-compatible endpoints
- Minimizes code changes - just swap base URL
- LangChain's `ChatOpenAI` already supports `openai_api_base` parameter
- Maintains single code path for both cloud and local

**Alternatives Considered**:
- Native Ollama Python SDK: More features but adds dependency and code paths
- LangChain Ollama integration: Separate code path, harder to maintain

### Decision 2: Provider Factory Pattern

**Choice**: Create `LLMProvider` factory that returns appropriate LLM instance based on configuration

```python
class LLMProviderType(Enum):
    OPENROUTER = "openrouter"
    OPENAI = "openai"  
    LOCAL = "local"  # Ollama, vLLM, etc.

def create_llm_provider(config: Settings) -> ChatModel:
    match config.llm_provider:
        case LLMProviderType.LOCAL:
            return ChatOpenAI(
                model=config.local_llm_model,
                openai_api_base=config.local_llm_base_url,
                openai_api_key="ollama",  # Dummy key for local
            )
        case LLMProviderType.OPENROUTER:
            ...
```

**Rationale**:
- Single instantiation point for all LLM usage
- Easy to add new providers
- Configuration-driven, no code changes needed

### Decision 3: Configurable Embedding Dimensions

**Choice**: Make embedding dimension configurable via environment variable with migration documentation

**Implementation**:
```python
# config.py
embedding_dimension: int = 1536  # Default for OpenAI
embedding_model: str = "openai/text-embedding-3-small"

# models.py - Dynamic dimension
from research_agent.config import get_settings
embedding: Mapped[Optional[List[float]]] = mapped_column(
    Vector(get_settings().embedding_dimension), nullable=True
)
```

**Migration Strategy**:
1. Changing embedding dimension requires database recreation
2. Document migration steps in README
3. Add startup validation: compare configured dimension vs database schema
4. Block startup if mismatch detected with clear error message

**Rationale**:
- Clean abstraction without runtime overhead
- Explicit migration better than implicit data corruption
- Common local models use different dimensions (768, 384, 1024)

### Decision 4: Local Model Context Windows

**Choice**: Extend `model_config.py` with local model configurations

```python
MODEL_CONTEXT_WINDOWS = {
    # Cloud models
    "openai/gpt-4o-mini": 128_000,
    ...
    # Local models
    "llama3.2:3b": 8_192,
    "llama3.1:8b": 32_768,
    "mistral:7b": 32_768,
    "qwen2.5:7b": 32_768,
    "phi3:mini": 4_096,
    "nomic-embed-text": 8_192,  # Embedding model
}
```

**Rationale**:
- Consistent with existing pattern
- Local models often have smaller context windows
- Essential for proper RAG context management

### Decision 5: Docker Compose Local Stack

**Choice**: Add optional Ollama service with volume mount for models

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: research-rag-ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    profiles:
      - local  # Only started with --profile local
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

**Rationale**:
- Profile-based: doesn't affect cloud deployment users
- GPU passthrough for NVIDIA cards
- Volume persistence for downloaded models

## Risks / Trade-offs

| Decision | Trade-off |
|----------|-----------|
| OpenAI-compatible API only | No access to Ollama-specific features (model management, etc.) |
| Dimension change requires DB recreation | Migration overhead, but ensures data consistency |
| Profile-based Docker services | Additional complexity for local users |
| Startup validation for dimensions | May block deployment if misconfigured |

## Migration Plan

### Phase 1: LLM Abstraction (No Breaking Changes)
1. Add `LLMProviderType` enum and factory function
2. Update `deps.py` to use factory
3. Add local LLM configuration options
4. Test with Ollama endpoint

### Phase 2: Embedding Abstraction (Potentially Breaking)
1. Add `embedding_dimension` config
2. Create local embedding service
3. Add dimension validation on startup
4. Document migration for dimension changes

### Phase 3: Docker Integration
1. Add Ollama service to docker-compose
2. Update docker-compose documentation
3. Add GPU support configuration

### Rollback
- Each phase is independently reversible
- Configuration defaults to OpenRouter behavior
- No automatic data migrations

## Open Questions

1. **Default local models**: Should we recommend specific Ollama models for RAG?
2. **Embedding model compatibility**: Should we include a compatibility matrix?
3. **CI testing**: How to test local model integration without GPU?
