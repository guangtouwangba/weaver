"""Flashcard generation agent."""

import json
from collections.abc import AsyncIterator
from typing import Any

from research_agent.domain.agents.base_agent import BaseOutputAgent, OutputEvent, OutputEventType
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.shared.utils.logger import logger


class FlashcardAgent(BaseOutputAgent):
    """Agent for generating flashcards from document content."""

    def __init__(
        self,
        llm_service: LLMService,
        max_tokens_per_request: int = 4000,
    ):
        super().__init__(llm_service, max_tokens_per_request)

    @property
    def output_type(self) -> str:
        return "flashcards"

    async def generate(
        self,
        document_content: str,
        document_title: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[OutputEvent]:
        """
        Generate flashcards from document content.
        """
        yield self._emit_started("Generating flashcards...")

        # Truncate content if too long
        truncated_content = self._truncate_content(document_content)
        title = document_title or "Untitled"

        prompt = f"""
You are an expert educational content creator. Your task is to create high-quality flashcards from the provided document content.

Document Title: {title}

Instructions:
1. Extract key concepts, definitions, dates, and important facts.
2. Create 10-20 flashcards depending on the content length and density.
3. Each flashcard must have a 'front' (question/term) and a 'back' (answer/definition).
4. Optionally add 'notes' for extra context.
5. Format the output as a valid JSON object with a 'cards' array.

Example JSON Format:
{{
  "cards": [
    {{
      "front": "What is the mitochondria?",
      "back": "The powerhouse of the cell.",
      "notes": "It generates most of the chemical energy needed to power the cell's biochemical reactions."
    }}
  ]
}}

Content:
{truncated_content}
"""

        messages = [
            ChatMessage(
                role="system",
                content="You are a helpful AI assistant that generates educational flashcards in JSON format.",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        yield self._emit_progress(0.1, message="Analyzing content...")

        try:
            # We use chat instead of generate since LLMService doesn't have generate with response_format in base
            # The prompt instructs JSON format, and we handle parsing
            response = await self._llm.chat(messages)

            yield self._emit_progress(0.8, message="Processing response...")

            # Parse JSON
            data = self._parse_json_response(response.content)

            if not data or "cards" not in data:
                yield self._emit_error("Failed to parse flashcard JSON response")
                return

            cards = data.get("cards", [])

            # Yield progress for each card processing (simulated)
            total_cards = len(cards)
            if total_cards > 0:
                for i, card in enumerate(cards):
                    # Validate card structure
                    if "front" not in card or "back" not in card:
                        continue

                    yield self._emit_progress(
                        0.8 + (0.1 * (i / total_cards)),
                        message=f"Created card {i+1}/{total_cards}",
                    )

            # Final result payload
            result_data = {
                "cards": cards,
                "documentTitle": title,
            }

            yield OutputEvent(
                type=OutputEventType.GENERATION_COMPLETE,
                node_data=result_data,
                message=f"Generated {len(cards)} flashcards",
            )

        except Exception as e:
            logger.error(f"Flashcard generation failed: {e}", exc_info=True)
            yield self._emit_error(str(e))

    def _parse_json_response(self, response: str) -> dict[str, Any] | None:
        """Parse JSON from LLM response, handling markdown code blocks."""
        content = response.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            first_newline = content.find("\n")
            if first_newline != -1:
                content = content[first_newline + 1 :]
            if content.endswith("```"):
                content = content[:-3].strip()
            elif "```" in content:
                content = content[: content.rfind("```")].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(
                f"[FlashcardAgent] JSON parse error: {e}, content: {content[:200]}"
            )
            return None

