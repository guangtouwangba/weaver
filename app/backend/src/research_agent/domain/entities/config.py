"""
Configuration Domain Entities.

These are pure data objects that represent configuration at runtime.
They are decoupled from the environment variable loading mechanism (pydantic-settings).
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RAGMode(str, Enum):
    """RAG operation mode."""

    TRADITIONAL = "traditional"  # Chunk-based retrieval
    LONG_CONTEXT = "long_context"  # Full document context (Mega-Prompt)
    AUTO = "auto"  # Automatically select based on document size


class RetrievalStrategyType(str, Enum):
    """Available retrieval strategy types."""

    VECTOR = "vector"  # Standard vector similarity search
    HYBRID = "hybrid"  # Vector + keyword search
    HYDE = "hyde"  # Hypothetical Document Embedding


class CitationFormat(str, Enum):
    """Citation format options."""

    INLINE = "inline"  # [doc_01] style
    STRUCTURED = "structured"  # XML <cite> style
    BOTH = "both"  # Support both formats


class IntentType(str, Enum):
    """Question intent types for adaptive RAG strategies."""

    FACTUAL = "factual"  # "什么是X"、"X的定义" - Needs precise matching
    CONCEPTUAL = "conceptual"  # "如何理解X"、"X的原理" - Needs detailed context
    COMPARISON = "comparison"  # "X和Y的区别"、"X vs Y" - Needs multiple docs
    HOWTO = "howto"  # "如何做X"、"X的步骤" - Needs procedural content
    SUMMARY = "summary"  # "总结X"、"X的要点" - Needs broad coverage
    EXPLANATION = "explanation"  # "为什么X"、"X的原因" - Needs causal chain


# -----------------------------------------------------------------------------
# Configuration Models (Pydantic BaseModel for validation & serialization)
# -----------------------------------------------------------------------------


class LLMConfig(BaseModel):
    """LLM configuration for generation."""

    model_name: str = Field(default="openai/gpt-4o-mini", description="LLM model identifier")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    api_base: Optional[str] = Field(default=None, description="Custom API base URL")
    api_key: Optional[str] = Field(default=None, description="API key (if not using env var)")

    class Config:
        frozen = True  # Immutable after creation


class EmbeddingConfig(BaseModel):
    """Embedding model configuration."""

    model_name: str = Field(
        default="openai/text-embedding-3-small", description="Embedding model identifier"
    )
    api_base: Optional[str] = Field(default=None, description="Custom API base URL")
    api_key: Optional[str] = Field(default=None, description="API key (if not using env var)")

    class Config:
        frozen = True


class RetrievalConfig(BaseModel):
    """Retrieval strategy configuration."""

    strategy_type: RetrievalStrategyType = Field(
        default=RetrievalStrategyType.VECTOR, description="Retrieval strategy to use"
    )
    top_k: int = Field(default=5, ge=1, le=100, description="Number of documents to retrieve")
    min_similarity: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Minimum similarity threshold"
    )
    use_hybrid_search: bool = Field(default=False, description="Enable hybrid (vector + keyword)")
    rerank_enabled: bool = Field(default=True, description="Enable LLM-based reranking")
    grading_enabled: bool = Field(default=True, description="Enable relevance grading")

    class Config:
        frozen = True


class GenerationConfig(BaseModel):
    """Generation strategy configuration."""

    style: str = Field(
        default="concise", description="Generation style: concise|detailed|structured"
    )
    max_length: int = Field(default=500, ge=50, le=4000, description="Max response length (tokens)")
    system_prompt: Optional[str] = Field(default=None, description="Custom system prompt override")
    citation_format: CitationFormat = Field(
        default=CitationFormat.BOTH, description="Citation format in responses"
    )

    class Config:
        frozen = True


class IntentClassificationConfig(BaseModel):
    """Intent classification configuration."""

    enabled: bool = Field(default=True, description="Enable intent-based adaptive strategies")
    cache_enabled: bool = Field(default=True, description="Cache classification results")

    class Config:
        frozen = True


class LongContextConfig(BaseModel):
    """Long context RAG configuration."""

    safety_ratio: float = Field(
        default=0.55, ge=0.1, le=0.9, description="Ratio of context window to use"
    )
    min_tokens: int = Field(
        default=10000, ge=1000, description="Minimum tokens to trigger long context mode"
    )
    enable_citation_grounding: bool = Field(
        default=True, description="Enable citation anchors in long context"
    )

    class Config:
        frozen = True


class RAGConfig(BaseModel):
    """
    Root RAG configuration object.

    This is the main configuration passed through the RAG pipeline.
    It aggregates all sub-configurations.
    """

    mode: RAGMode = Field(default=RAGMode.TRADITIONAL, description="RAG operation mode")
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM configuration")
    embedding: EmbeddingConfig = Field(
        default_factory=EmbeddingConfig, description="Embedding configuration"
    )
    retrieval: RetrievalConfig = Field(
        default_factory=RetrievalConfig, description="Retrieval configuration"
    )
    generation: GenerationConfig = Field(
        default_factory=GenerationConfig, description="Generation configuration"
    )
    intent_classification: IntentClassificationConfig = Field(
        default_factory=IntentClassificationConfig, description="Intent classification config"
    )
    long_context: LongContextConfig = Field(
        default_factory=LongContextConfig, description="Long context mode configuration"
    )

    class Config:
        frozen = True

    @classmethod
    def from_intent(
        cls, intent_type: IntentType, base_config: Optional["RAGConfig"] = None
    ) -> "RAGConfig":
        """
        Create a RAGConfig optimized for a specific intent type.

        Args:
            intent_type: The classified intent type
            base_config: Optional base configuration to extend

        Returns:
            RAGConfig tuned for the intent
        """
        # Intent-specific strategy mappings
        intent_strategies = {
            IntentType.FACTUAL: {
                "retrieval": RetrievalConfig(
                    top_k=3,
                    min_similarity=0.7,
                    use_hybrid_search=True,
                    strategy_type=RetrievalStrategyType.HYBRID,
                ),
                "generation": GenerationConfig(
                    style="concise",
                    max_length=150,
                    system_prompt="You are a research assistant. Provide a concise, factual answer (1-2 sentences). Be direct and precise.",
                ),
            },
            IntentType.CONCEPTUAL: {
                "retrieval": RetrievalConfig(
                    top_k=8,
                    min_similarity=0.5,
                    use_hybrid_search=False,
                    strategy_type=RetrievalStrategyType.VECTOR,
                ),
                "generation": GenerationConfig(
                    style="detailed",
                    max_length=500,
                    system_prompt="You are a research assistant. Provide a detailed explanation with principles and examples. Help the user understand the concept deeply.",
                ),
            },
            IntentType.COMPARISON: {
                "retrieval": RetrievalConfig(
                    top_k=10,
                    min_similarity=0.6,
                    use_hybrid_search=True,
                    strategy_type=RetrievalStrategyType.HYBRID,
                ),
                "generation": GenerationConfig(
                    style="structured",
                    max_length=400,
                    system_prompt="You are a research assistant. Compare the items using a clear structure (table or bullet points). Highlight key similarities and differences.",
                ),
            },
            IntentType.HOWTO: {
                "retrieval": RetrievalConfig(
                    top_k=5,
                    min_similarity=0.6,
                    use_hybrid_search=True,
                    strategy_type=RetrievalStrategyType.HYBRID,
                ),
                "generation": GenerationConfig(
                    style="structured",
                    max_length=400,
                    system_prompt="You are a research assistant. Provide step-by-step instructions in a numbered list format. Be clear and actionable.",
                ),
            },
            IntentType.SUMMARY: {
                "retrieval": RetrievalConfig(
                    top_k=15,
                    min_similarity=0.4,
                    use_hybrid_search=False,
                    strategy_type=RetrievalStrategyType.VECTOR,
                ),
                "generation": GenerationConfig(
                    style="structured",
                    max_length=500,
                    system_prompt="You are a research assistant. Provide a comprehensive summary with key points in bullet format. Cover all important aspects.",
                ),
            },
            IntentType.EXPLANATION: {
                "retrieval": RetrievalConfig(
                    top_k=8,
                    min_similarity=0.5,
                    use_hybrid_search=False,
                    strategy_type=RetrievalStrategyType.VECTOR,
                ),
                "generation": GenerationConfig(
                    style="detailed",
                    max_length=500,
                    system_prompt="You are a research assistant. Explain the reasoning and causality. Help the user understand why and how things work.",
                ),
            },
        }

        strategy = intent_strategies.get(intent_type, intent_strategies[IntentType.FACTUAL])

        if base_config:
            # Merge with base config
            return cls(
                mode=base_config.mode,
                llm=base_config.llm,
                embedding=base_config.embedding,
                retrieval=strategy["retrieval"],
                generation=strategy["generation"],
                intent_classification=base_config.intent_classification,
                long_context=base_config.long_context,
            )
        else:
            return cls(
                retrieval=strategy["retrieval"],
                generation=strategy["generation"],
            )
