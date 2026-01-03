# Infrastructure Capability

## ADDED Requirements

### Requirement: Local Deployment Configuration
The system SHALL support configuration for local AI service deployment through environment variables.

#### Scenario: Configure local LLM endpoint
- **WHEN** user sets `LLM_PROVIDER_TYPE=local`, `LOCAL_LLM_BASE_URL=http://localhost:11434/v1`, and `LOCAL_LLM_MODEL=llama3.2:3b`
- **THEN** the system SHALL connect to the specified local LLM endpoint for all chat completions

#### Scenario: Configure local embedding endpoint  
- **WHEN** user sets `EMBEDDING_PROVIDER_TYPE=local` and `LOCAL_EMBEDDING_MODEL=nomic-embed-text`
- **THEN** the system SHALL use the local embedding service for all vector operations

#### Scenario: Default to cloud provider
- **WHEN** no `LLM_PROVIDER_TYPE` is specified
- **THEN** the system SHALL use OpenRouter as the default LLM provider

---

### Requirement: Docker Compose Local Stack
The system SHALL provide optional Docker Compose services for fully local deployment.

#### Scenario: Start local AI services
- **WHEN** user runs `docker-compose --profile local up`
- **THEN** the system SHALL start Ollama alongside PostgreSQL

#### Scenario: GPU acceleration support
- **WHEN** Ollama service is started on a machine with NVIDIA GPU
- **THEN** the system SHALL pass through GPU resources to the container for accelerated inference

#### Scenario: Model persistence
- **WHEN** Ollama downloads a model
- **THEN** the model SHALL be persisted in a Docker volume and survive container restarts

---

### Requirement: Embedding Dimension Validation
The system SHALL validate embedding dimension configuration at startup.

#### Scenario: Dimension mismatch detection
- **WHEN** configured `EMBEDDING_DIMENSION` differs from database schema
- **THEN** the system SHALL fail startup with a clear error message explaining the mismatch and migration steps

#### Scenario: Dimension consistency
- **WHEN** `EMBEDDING_DIMENSION` matches database vector column size
- **THEN** the system SHALL start normally without warnings
