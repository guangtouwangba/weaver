"""
Basic Generation Strategy.

Standard RAG generation using retrieved context chunks.
"""

from typing import Any, AsyncIterator

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from research_agent.domain.entities.config import GenerationConfig, LLMConfig
from research_agent.domain.strategies.base import GenerationResult, IGenerationStrategy
from research_agent.shared.utils.logger import logger

# Default system prompt for RAG
DEFAULT_SYSTEM_PROMPT = """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise."""


class BasicGenerationStrategy(IGenerationStrategy):
    """
    Basic RAG generation strategy.

    Uses retrieved document chunks as context to generate answers.
    Supports customizable system prompts and generation styles.
    """

    def __init__(self, llm: ChatOpenAI | None = None):
        """
        Initialize basic generation strategy.

        Args:
            llm: Optional pre-configured LLM instance.
                 If not provided, will be created from config.
        """
        self._llm = llm

    @property
    def name(self) -> str:
        return "basic"

    def _get_llm(self, llm_config: LLMConfig) -> ChatOpenAI:
        """Get or create LLM instance from config."""
        if self._llm:
            return self._llm

        # Create LLM from config
        return ChatOpenAI(
            model=llm_config.model_name,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens,
            openai_api_key=llm_config.api_key,
            openai_api_base=llm_config.api_base or "https://openrouter.ai/api/v1",
        )

    def _get_system_prompt(self, config: GenerationConfig) -> str:
        """Get system prompt based on configuration."""
        if config.system_prompt:
            return config.system_prompt

        # Style-based prompts
        style_prompts = {
            "concise": """You are a research assistant. Provide a concise, factual answer (1-2 sentences). Be direct and precise.
Use the following context to answer the question. If you don't know, say so.""",
            "detailed": """You are a research assistant. Provide a detailed explanation with principles and examples.
Use the following context to answer the question. Help the user understand deeply.""",
            "structured": """You are a research assistant. Provide a well-structured answer using bullet points or numbered lists.
Use the following context to answer the question. Be clear and organized.""",
        }

        return style_prompts.get(config.style, DEFAULT_SYSTEM_PROMPT)

    async def generate(
        self,
        query: str,
        context: str,
        config: GenerationConfig,
        llm_config: LLMConfig,
        **kwargs: Any,
    ) -> GenerationResult:
        """
        Generate an answer from query and context.

        Args:
            query: User question
            context: Retrieved context (concatenated document chunks)
            config: Generation configuration
            llm_config: LLM model configuration
            **kwargs: Additional parameters (chat_history, etc.)

        Returns:
            GenerationResult containing the answer
        """
        logger.info(
            f"[BasicGeneration] Generating with style={config.style}, "
            f"context_length={len(context)} chars"
        )

        llm = self._get_llm(llm_config)
        system_prompt = self._get_system_prompt(config)

        # Build prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "Question: {question}\n\nContext: {context}\n\nAnswer:"),
            ]
        )

        chain = prompt | llm | StrOutputParser()

        try:
            generation = await chain.ainvoke(
                {
                    "question": query,
                    "context": context,
                }
            )

            logger.info(f"[BasicGeneration] Generated {len(generation)} chars")

            return GenerationResult(
                content=generation,
                citations=[],  # Basic strategy doesn't parse citations
                metadata={
                    "style": config.style,
                    "context_length": len(context),
                },
                strategy_name=self.name,
            )

        except Exception as e:
            logger.error(f"[BasicGeneration] Failed: {e}", exc_info=True)
            return GenerationResult(
                content="I encountered an error while generating the response. Please try again.",
                citations=[],
                metadata={"error": str(e)},
                strategy_name=self.name,
            )

    async def stream(
        self,
        query: str,
        context: str,
        config: GenerationConfig,
        llm_config: LLMConfig,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream generation token by token.

        Args:
            query: User question
            context: Retrieved context
            config: Generation configuration
            llm_config: LLM model configuration
            **kwargs: Additional parameters

        Yields:
            Generated tokens
        """
        logger.info(f"[BasicGeneration] Streaming response...")

        llm = self._get_llm(llm_config)
        system_prompt = self._get_system_prompt(config)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "Question: {question}\n\nContext: {context}\n\nAnswer:"),
            ]
        )

        # Enable streaming
        streaming_llm = llm.with_config({"streaming": True})
        chain = prompt | streaming_llm | StrOutputParser()

        try:
            async for token in chain.astream(
                {
                    "question": query,
                    "context": context,
                }
            ):
                yield token

        except Exception as e:
            logger.error(f"[BasicGeneration] Stream error: {e}", exc_info=True)
            yield f"\n\n[Error: {str(e)}]"
