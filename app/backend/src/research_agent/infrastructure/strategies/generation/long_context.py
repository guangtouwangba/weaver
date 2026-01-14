"""
Long Context Generation Strategy.

Uses full document content with citation grounding (Mega-Prompt approach).
"""

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from research_agent.domain.entities.config import CitationFormat, GenerationConfig, LLMConfig
from research_agent.domain.strategies.base import GenerationResult, IGenerationStrategy
from research_agent.shared.utils.logger import logger

# Long context system prompt with citation instructions
LONG_CONTEXT_SYSTEM_PROMPT = """You are a research assistant with access to full document content.
Your task is to answer questions using the provided documents with precise citations.

Citation Rules:
1. Use [doc_XX] format for inline citations (e.g., [doc_01])
2. Every factual claim must be cited
3. If information spans multiple documents, cite all relevant sources
4. If the answer cannot be found in the documents, explicitly state this

Response Format:
- Begin with a direct answer
- Support with evidence from documents
- End with a brief summary if appropriate"""


class LongContextGenerationStrategy(IGenerationStrategy):
    """
    Long context generation strategy for Mega-Prompt approach.

    Uses full document content instead of chunks, with citation grounding.
    Best for:
    - Documents that fit within context window
    - Questions requiring cross-document reasoning
    - High-fidelity citation requirements
    """

    def __init__(self, llm: ChatOpenAI | None = None):
        """
        Initialize long context generation strategy.

        Args:
            llm: Optional pre-configured LLM instance.
        """
        self._llm = llm

    @property
    def name(self) -> str:
        return "long_context"

    def _get_llm(self, llm_config: LLMConfig) -> ChatOpenAI:
        """Get or create LLM instance from config."""
        if self._llm:
            return self._llm

        return ChatOpenAI(
            model=llm_config.model_name,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens,
            openai_api_key=llm_config.api_key,
            openai_api_base=llm_config.api_base or "https://openrouter.ai/api/v1",
        )

    def _build_prompt(
        self,
        query: str,
        documents: list[dict],
        citation_format: CitationFormat,
    ) -> str:
        """
        Build the Mega-Prompt with full document content.

        Args:
            query: User question
            documents: List of document dicts with id, filename, content
            citation_format: Citation format preference

        Returns:
            Formatted prompt string
        """
        # Build documents section
        doc_sections = []
        for i, doc in enumerate(documents, 1):
            doc_id = doc.get("document_id", f"doc_{i:02d}")
            filename = doc.get("filename", f"Document {i}")
            content = doc.get("content", "")
            page_count = doc.get("page_count", 0)

            section = f"--- Document {i}: {filename} (ID: {doc_id}"
            if page_count > 0:
                section += f", {page_count} pages"
            section += f") ---\n\n{content}"
            doc_sections.append(section)

        documents_text = "\n\n".join(doc_sections)

        # Citation format instructions
        citation_instructions = {
            CitationFormat.INLINE: "Use [doc_XX] format for citations.",
            CitationFormat.STRUCTURED: "Use <cite doc_id='XX' page='Y'>quote</cite> format.",
            CitationFormat.BOTH: "Use both [doc_XX] inline and structured <cite> tags.",
        }

        citation_text = citation_instructions.get(
            citation_format, citation_instructions[CitationFormat.BOTH]
        )

        return f"""Documents:
{documents_text}

Citation Format: {citation_text}

Question: {query}

Please provide a comprehensive answer with citations."""

    def _parse_citations(self, text: str) -> list[dict]:
        """
        Parse citations from generated text.

        Extracts both [doc_XX] and <cite> style citations.
        """
        import re

        citations = []

        # Parse inline citations [doc_XX]
        inline_pattern = r"\[doc_(\d+)\]"
        for match in re.finditer(inline_pattern, text):
            citations.append(
                {
                    "type": "inline",
                    "document_id": f"doc_{match.group(1)}",
                    "position": match.start(),
                }
            )

        # Parse structured citations <cite doc_id='XX' page='Y'>quote</cite>
        struct_pattern = (
            r"<cite\s+doc_id=['\"]([^'\"]+)['\"](?:\s+page=['\"]([^'\"]+)['\"])?>([^<]*)</cite>"
        )
        for match in re.finditer(struct_pattern, text):
            citations.append(
                {
                    "type": "structured",
                    "document_id": match.group(1),
                    "page_number": match.group(2),
                    "snippet": match.group(3),
                    "position": match.start(),
                }
            )

        return citations

    async def generate(
        self,
        query: str,
        context: str,
        config: GenerationConfig,
        llm_config: LLMConfig,
        **kwargs: Any,
    ) -> GenerationResult:
        """
        Generate answer using long context mode.

        Args:
            query: User question
            context: Full document content (pre-formatted) or raw context
            config: Generation configuration
            llm_config: LLM model configuration
            **kwargs: Additional parameters
                - documents: List of document dicts for structured prompt building

        Returns:
            GenerationResult with answer and parsed citations
        """
        documents = kwargs.get("documents", [])

        logger.info(
            f"[LongContextGeneration] Generating with {len(documents)} documents, "
            f"context_length={len(context)} chars"
        )

        llm = self._get_llm(llm_config)

        # Build prompt
        if documents:
            user_prompt = self._build_prompt(query, documents, config.citation_format)
        else:
            # Fallback: use raw context
            user_prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer with citations:"

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", LONG_CONTEXT_SYSTEM_PROMPT),
                ("human", user_prompt),
            ]
        )

        chain = prompt | llm | StrOutputParser()

        try:
            generation = await chain.ainvoke({})

            # Parse citations from response
            citations = self._parse_citations(generation)

            logger.info(
                f"[LongContextGeneration] Generated {len(generation)} chars, "
                f"{len(citations)} citations"
            )

            return GenerationResult(
                content=generation,
                citations=citations,
                metadata={
                    "document_count": len(documents),
                    "context_length": len(context),
                    "citation_count": len(citations),
                },
                strategy_name=self.name,
            )

        except Exception as e:
            logger.error(f"[LongContextGeneration] Failed: {e}", exc_info=True)
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
        Stream long context generation token by token.
        """
        documents = kwargs.get("documents", [])

        logger.info("[LongContextGeneration] Streaming response...")

        llm = self._get_llm(llm_config)

        if documents:
            user_prompt = self._build_prompt(query, documents, config.citation_format)
        else:
            user_prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer with citations:"

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", LONG_CONTEXT_SYSTEM_PROMPT),
                ("human", user_prompt),
            ]
        )

        streaming_llm = llm.with_config({"streaming": True})
        chain = prompt | streaming_llm | StrOutputParser()

        try:
            async for token in chain.astream({}):
                yield token

        except Exception as e:
            logger.error(f"[LongContextGeneration] Stream error: {e}", exc_info=True)
            yield f"\n\n[Error: {str(e)}]"
