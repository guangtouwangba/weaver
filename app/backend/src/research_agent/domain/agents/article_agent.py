"""Article generation agent for Magic Cursor."""

import json
from collections.abc import AsyncIterator
from typing import Any

from research_agent.domain.agents.base_agent import BaseOutputAgent, OutputEvent, OutputEventType
from research_agent.domain.entities.output import ArticleData, ArticleSection, SourceRef
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.infrastructure.llm.prompts import PromptLoader
from research_agent.shared.utils.logger import logger

# Template paths
ARTICLE_SYSTEM_TEMPLATE = "agents/article/system.j2"
ARTICLE_GENERATION_TEMPLATE = "agents/article/generation.j2"


class ArticleAgent(BaseOutputAgent):
    """
    Agent for generating structured articles from canvas node content.

    Used by Magic Cursor "Draft Article" action.

    Generation Strategy:
    1. Collect content from all selected canvas nodes
    2. Analyze themes and structure
    3. Generate article with sections
    4. Include source attribution
    """

    def __init__(
        self,
        llm_service: LLMService,
        max_tokens_per_request: int = 4000,
        skills: list[Any] = None,
    ):
        super().__init__(llm_service, max_tokens_per_request)
        self._skills = skills or []
        self._prompt_loader = PromptLoader.get_instance()

    @property
    def output_type(self) -> str:
        return "article"

    async def generate(
        self,
        document_content: str,
        document_title: str | None = None,
        skills: list[Any] = None,
        **kwargs: Any,
    ) -> AsyncIterator[OutputEvent]:
        """
        Generate article from node content.

        Args:
            document_content: Combined content from canvas nodes
            document_title: Optional title for the article
            **kwargs:
                - node_data: List of {id, title, content} for source attribution
                - snapshot_context: Selection box coordinates for refresh

        Yields:
            OutputEvent instances as generation progresses
        """
        node_data: list[dict[str, Any]] = kwargs.get("node_data", [])
        snapshot_context: dict[str, Any] | None = kwargs.get("snapshot_context")
        current_skills = skills if skills is not None else self._skills

        logger.info(f"[ArticleAgent] Starting article generation from {len(node_data)} nodes")

        yield self._emit_started("Starting article generation...")

        try:
            # Format node content for the prompt
            node_content_str = self._format_node_content(node_data, document_content)

            # Truncate if necessary
            content = self._truncate_content(node_content_str)

            yield self._emit_progress(0.2, message="Analyzing content structure...")

            # Build prompt using Jinja2 templates
            user_prompt = self._prompt_loader.render(
                ARTICLE_GENERATION_TEMPLATE,
                node_content=content,
                skills=current_skills,
            )

            system_prompt = self._prompt_loader.render(
                ARTICLE_SYSTEM_TEMPLATE,
                skills=current_skills,
            )

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]

            yield self._emit_progress(0.4, message="Generating article...")

            # Generate article
            logger.info("[ArticleAgent] Calling LLM for article generation")
            response = await self._llm.chat(messages)

            yield self._emit_progress(0.8, message="Processing article...")

            # Parse response
            article_data = self._parse_article_response(response.content, snapshot_context)

            if article_data is None:
                raise ValueError("Failed to parse article response from LLM")

            logger.info(
                f"[ArticleAgent] Generated article with {len(article_data.sections)} sections"
            )

            # Emit complete with article data
            yield OutputEvent(
                type=OutputEventType.GENERATION_COMPLETE,
                message="Article generation complete",
                node_data=article_data.to_dict(),
            )

        except Exception as e:
            logger.error(f"[ArticleAgent] Generation failed: {e}", exc_info=True)
            yield self._emit_error(f"Article generation failed: {str(e)}")

    def _format_node_content(self, node_data: list[dict[str, Any]], fallback_content: str) -> str:
        """Format node data for the prompt."""
        if not node_data:
            return fallback_content

        parts = []
        for node in node_data:
            node_id = node.get("id", "unknown")
            node_title = node.get("title", "Untitled")
            node_content = node.get("content", "")

            parts.append(f"--- Node: {node_id} ---")
            parts.append(f"Title: {node_title}")
            if node_content:
                parts.append(f"Content:\n{node_content}")
            parts.append("")

        return "\n".join(parts)

    def _parse_article_response(
        self,
        response: str,
        snapshot_context: dict[str, Any] | None,
    ) -> ArticleData | None:
        """Parse the LLM response into ArticleData."""
        try:
            response_text = response.strip()

            # Handle markdown code blocks
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.startswith("```") and not in_code_block:
                        in_code_block = True
                        continue
                    elif line.startswith("```") and in_code_block:
                        break
                    elif in_code_block:
                        json_lines.append(line)
                response_text = "\n".join(json_lines)

            data = json.loads(response_text)

            # Extract sections
            sections = []
            for s in data.get("sections", []):
                sections.append(
                    ArticleSection(
                        heading=s.get("heading", "Section"),
                        content=s.get("content", ""),
                    )
                )

            # Extract source refs
            source_refs = []
            for ref in data.get("sourceRefs", []):
                source_refs.append(
                    SourceRef(
                        source_id=ref.get("sourceId", ""),
                        source_type=ref.get("sourceType", "node"),
                        location=ref.get("location"),
                        quote=ref.get("quote", ""),
                    )
                )

            return ArticleData(
                title=data.get("title", "Generated Article"),
                sections=sections,
                source_refs=source_refs,
                snapshot_context=snapshot_context,
            )

        except json.JSONDecodeError as e:
            logger.error(f"[ArticleAgent] JSON parse error: {e}")
            logger.debug(f"[ArticleAgent] Raw response: {response[:500]}...")

            # Fallback: treat response as article content
            if len(response) > 100:
                return ArticleData(
                    title="Generated Article",
                    sections=[
                        ArticleSection(
                            heading="Content",
                            content=response[:2000],
                        )
                    ],
                    source_refs=[],
                    snapshot_context=snapshot_context,
                )

            return None

        except Exception as e:
            logger.error(f"[ArticleAgent] Parse error: {e}", exc_info=True)
            return None
