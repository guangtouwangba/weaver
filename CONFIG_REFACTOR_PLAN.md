# Configuration System Refactoring Plan

## 1. Objectives
- **Decouple**: Remove dependency on global `get_settings()` in business logic (`rag_graph.py`).
- **Dynamic**: Support request-level configuration (e.g., per-user LLM model selection).
- **Layered**: Implement configuration hierarchy: User > Project > System Default.
- **Extensible**: Use **Factory + Strategy Patterns** to easily integrate new RAG algorithms (e.g., HyDE, GraphRAG) without modifying core graph logic.
- **Clean**: Use dependency injection and define configuration as Domain Entities.

## 2. Architecture Design

### Domain Layer (New)
Define configuration data shapes and strategy interfaces.
- **Configuration Models** (`domain/entities/config.py`):
  - `LLMConfig`: `model_name`, `temperature`, `api_base`, etc.
  - `RetrievalConfig`: `top_k`, `min_similarity`, `strategy_name` (e.g., "vector", "hybrid", "hyde").
  - `RAGConfig`: `mode`, `citation_format`, `retrieval_config`, `llm_config`.
  - `AppConfig`: Root object.

- **Strategy Interfaces** (`domain/strategies/base.py`):
  - `IRetrievalStrategy`: Abstract base class with `async def retrieve(query: str, config: RetrievalConfig) -> List[Document]`.
  - `IGenerationStrategy`: Abstract base class with `async def generate(query: str, context: str, config: LLMConfig) -> str`.

### Service Layer (New)
Logic to resolve configs and provide strategies.
- **ConfigurationService** (`domain/services/config_service.py`):
  - `get_config(user_id, project_id) -> AppConfig`
  - Logic: Load System Env -> Merge Project DB Config -> Merge User DB Config.

- **StrategyFactory** (`domain/services/strategy_factory.py`):
  - `get_retrieval_strategy(name: str) -> IRetrievalStrategy`
  - `get_generation_strategy(name: str) -> IGenerationStrategy`
  - Uses a registry pattern to map names to implementation classes.

### Application Layer (Refactor)
The RAG graph becomes a coordinator, delegating actual work to strategies.
- **File**: `app/backend/src/research_agent/application/graphs/rag_graph.py`
- **Changes**:
  - **GraphState**: Include `config: AppConfig`.
  - **Node - Retrieve**:
    ```python
    def retrieve(state):
        config = state['config']
        strategy = StrategyFactory.get_retrieval_strategy(config.retrieval.strategy_name)
        documents = await strategy.retrieve(state['question'], config.retrieval)
        return {"documents": documents}
    ```
  - **Node - Generate**: Delegate to `IGenerationStrategy`.

### Infrastructure Layer (Enhance)
Implement concrete strategies and adapters.
- **Retrieval Strategies** (`infrastructure/strategies/retrieval/`):
  - `VectorRetrievalStrategy`: Standard PGVector search.
  - `HybridRetrievalStrategy`: Vector + Keyword search.
  - `HyDERetrievalStrategy`: Generate hypothetical document then vector search.
- **LLM Components**:
  - `LLMFactory`: Create LangChain objects from `LLMConfig`.

## 3. Implementation Steps

### Phase 1: Domain & Service Foundation ✅ COMPLETED
1. ✅ Create `domain/entities/config.py` with Pydantic models.
2. ✅ Define `IRetrievalStrategy` and `IGenerationStrategy` interfaces (`domain/strategies/base.py`).
3. ✅ Create `domain/services/config_service.py` (Configuration resolution).
4. ✅ Create `domain/services/strategy_factory.py` (Strategy instantiation).

### Phase 2: Concrete Strategies ✅ COMPLETED
5. ✅ Implement `VectorRetrievalStrategy`, `HybridRetrievalStrategy` (`infrastructure/strategies/retrieval/`).
6. ✅ Implement `BasicGenerationStrategy`, `LongContextGenerationStrategy` (`infrastructure/strategies/generation/`).

### Phase 3: Application Logic Migration ✅ COMPLETED
7. ✅ Create `rag_graph_v2.py` with strategy-based implementation.
8. ✅ New `RAGGraphState` includes `config: dict` (RAGConfig serialized).
9. ✅ `RAGGraphDependencies` for dependency injection of strategies.
   - *Note*: Original `rag_graph.py` preserved for backward compatibility.

### Phase 4: Database Integration ✅ COMPLETED
9. ✅ Implement database models for configs (`GlobalSettingModel`, `ProjectSettingModel`).
10. ✅ Create migration file `20241207_000002_add_settings_tables.py`.
11. ✅ Implement `ISettingsRepository` interface and `SQLAlchemySettingsRepository`.
12. ✅ Implement `EncryptionService` for API key encryption.
13. ✅ Create `SettingsService` for business logic.
14. ✅ Create REST API endpoints (`/api/v1/settings/*`).
15. ✅ Create `AsyncConfigurationService` with DB support.

## 4. Example: Before vs After

**Before (Procedural & Coupled):**
```python
# rag_graph.py
def retrieve(state):
    settings = get_settings()
    if settings.use_hybrid:
        # ... 20 lines of hybrid logic ...
    else:
        # ... 10 lines of vector logic ...
```

**After (Polymorphic & Decoupled):**
```python
# rag_graph.py
def retrieve(state):
    config = state["config"]
    # The factory decides WHICH class to instantiate based on config
    strategy = StrategyFactory.get_retriever(config.retrieval.strategy_type)
    # Polymorphic call - graph doesn't care if it's Hybrid or Vector
    docs = await strategy.retrieve(state["question"], config.retrieval)
    return {"documents": docs}
```