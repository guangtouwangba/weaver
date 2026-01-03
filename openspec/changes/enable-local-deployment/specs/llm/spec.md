# LLM Capability

## ADDED Requirements

### Requirement: LLM Provider Factory
The system SHALL use a factory pattern to create LLM instances based on configuration.

#### Scenario: Create OpenRouter LLM
- **WHEN** `LLM_PROVIDER_TYPE=openrouter`
- **THEN** the factory SHALL return a ChatOpenAI instance configured for OpenRouter API

#### Scenario: Create local LLM
- **WHEN** `LLM_PROVIDER_TYPE=local`
- **THEN** the factory SHALL return a ChatOpenAI instance with base URL pointing to local Ollama endpoint

#### Scenario: Fallback model selection
- **WHEN** configured model is not found in context window registry
- **THEN** the system SHALL use conservative default context window (8192 tokens)

---

### Requirement: Local Model Context Windows
The system SHALL maintain context window sizes for common local models.

#### Scenario: Llama model context
- **WHEN** using `llama3.2:3b` model
- **THEN** the system SHALL use 8192 token context window limit

#### Scenario: Unknown local model
- **WHEN** using an unregistered local model
- **THEN** the system SHALL use 8192 token conservative default and log a warning

#### Scenario: Context budget calculation
- **WHEN** calculating available tokens for RAG context
- **THEN** the system SHALL apply safety ratio (default 55%) to model's context window

---

### Requirement: Embedding Provider Factory
The system SHALL use a factory pattern to create embedding service instances.

#### Scenario: Create local embedding service
- **WHEN** `EMBEDDING_PROVIDER_TYPE=local`
- **THEN** the factory SHALL return embedding service using Ollama's /api/embeddings endpoint

#### Scenario: Dimension from configuration
- **WHEN** creating embedding service
- **THEN** the service SHALL use `EMBEDDING_DIMENSION` from configuration for vector operations

#### Scenario: OpenRouter embedding fallback
- **WHEN** `EMBEDDING_PROVIDER_TYPE=openrouter` or not specified
- **THEN** the factory SHALL return OpenRouter embedding service with 1536 dimensions
