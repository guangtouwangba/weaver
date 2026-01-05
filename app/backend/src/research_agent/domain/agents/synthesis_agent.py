"""Agent for synthesizing multiple content sources into consolidated insights.

Implements a multi-step reasoning pipeline:
1. Reasoning: Analyze domains and identify potential conceptual bridges
2. Drafting: Generate initial synthesis based on reasoning
3. Review: Self-critique the draft for quality
4. Refinement: Improve the draft based on critique
"""

import json
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

from research_agent.domain.agents.base_agent import BaseOutputAgent, OutputEvent, OutputEventType
from research_agent.domain.agents.synthesis_prompts import (
    DRAFTING_PROMPTS,
    REASONING_PROMPT,
    REFINEMENT_PROMPT,
    REVIEW_PROMPT,
)
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.shared.utils.logger import logger


class SynthesisAgent(BaseOutputAgent):
    """
    Agent for synthesizing multiple content sources into consolidated insights.

    Uses a multi-step reasoning pipeline to generate deep, well-reviewed insights
    that identify connections, themes, and actionable recommendations.
    """

    def __init__(
        self,
        llm_service: LLMService,
        max_tokens_per_request: int = 4000,
    ):
        """
        Initialize the synthesis agent.

        Args:
            llm_service: LLM service for text generation
            max_tokens_per_request: Maximum tokens per request
        """
        super().__init__(llm_service, max_tokens_per_request)

    @property
    def output_type(self) -> str:
        """Return the output type this agent generates."""
        return "synthesis"

    async def generate(
        self,
        document_content: str,
        document_title: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[OutputEvent]:
        """
        Not used for synthesis - use synthesize() instead.

        This is required by base class but synthesis uses a different entry point.
        """
        yield self._emit_error("Use synthesize() method for synthesis operations")

    async def synthesize(
        self,
        input_contents: List[str],
        source_ids: Optional[List[str]] = None,
        mode: str = "connect",
    ) -> AsyncIterator[OutputEvent]:
        """
        Synthesize multiple content sources into a consolidated insight.

        Uses a 4-step pipeline:
        1. Reasoning - Analyze domains and find potential bridges
        2. Drafting - Generate initial insight
        3. Review - Self-critique for quality
        4. Refinement - Improve based on critique

        Args:
            input_contents: List of content strings to synthesize
            source_ids: Optional list of IDs for the source nodes (for metadata)
            mode: Synthesis mode (connect, inspire, debate)

        Yields:
            OutputEvent instances as synthesis progresses
        """
        if len(input_contents) < 2:
            yield self._emit_error("At least 2 inputs are required for synthesis")
            return

        logger.info(
            f"[SynthesisAgent] Starting deep synthesis of {len(input_contents)} inputs with mode={mode}"
        )
        yield self._emit_started(f"Synthesizing {len(input_contents)} sources ({mode})")

        try:
            # Format inputs for prompts
            formatted_inputs = self._format_inputs(input_contents)

            # Step 1: Reasoning (Domain & Link Analysis)
            yield self._emit_progress(
                0.1, message="🤔 Thinking... analyzing domains and connections"
            )
            reasoning = await self._reason_about_inputs(formatted_inputs)
            logger.debug(f"[SynthesisAgent] Reasoning complete: {reasoning[:200]}...")

            # Step 2: Drafting (Initial Insight)
            yield self._emit_progress(0.35, message="✍️ Drafting initial insight...")
            draft = await self._draft_synthesis(formatted_inputs, reasoning, mode)
            if draft is None:
                yield self._emit_error("Failed to generate initial draft")
                return
            logger.debug(f"[SynthesisAgent] Draft complete: {draft.get('title', 'N/A')}")

            # Step 3: Review (Self-Critique)
            yield self._emit_progress(0.6, message="🔍 Reviewing and critiquing...")
            critique = await self._review_draft(formatted_inputs, draft)
            logger.debug(f"[SynthesisAgent] Critique complete: {critique[:200]}...")

            # Step 4: Refinement (Final Output)
            yield self._emit_progress(0.85, message="✨ Refining final insight...")
            final_synthesis = await self._refine_draft(draft, critique)
            if final_synthesis is None:
                # Fall back to draft if refinement fails
                logger.warning("[SynthesisAgent] Refinement failed, using draft")
                final_synthesis = draft

            # Create a node for the synthesis result
            node_id = f"synthesis-{uuid4().hex[:8]}"
            node_data = {
                "id": node_id,
                "label": final_synthesis.get("title", "Consolidated Insight"),
                "content": self._format_node_content(final_synthesis),
                "type": "synthesis",
                "metadata": {
                    "source_node_ids": source_ids or [],
                    "synthesis_mode": mode,
                    "confidence": final_synthesis.get("confidence", "medium"),
                    "themes": final_synthesis.get("supporting_themes", []),
                    "reasoning_used": True,  # Indicates deep synthesis was used
                },
                "status": "complete",
            }

            yield self._emit_node_added(node_id, node_data)
            yield self._emit_progress(1.0, message="Synthesis complete")

            # Emit complete event
            yield OutputEvent(
                type=OutputEventType.GENERATION_COMPLETE,
                message=f"Synthesized {len(input_contents)} sources with deep reasoning",
                node_data=final_synthesis,
            )

            logger.info(
                f"[SynthesisAgent] Deep synthesis complete: {final_synthesis.get('title', 'N/A')}"
            )

        except Exception as e:
            logger.error(f"[SynthesisAgent] Synthesis failed: {e}", exc_info=True)
            yield self._emit_error(str(e))

    # =========================================================================
    # Pipeline Step Methods
    # =========================================================================

    async def _reason_about_inputs(self, formatted_inputs: str) -> str:
        """
        Step 1: Analyze domains and identify potential conceptual bridges.

        Args:
            formatted_inputs: Formatted input contents

        Returns:
            Reasoning trace as plain text
        """
        prompt = REASONING_PROMPT.format(inputs=formatted_inputs)
        prompt = self._truncate_content(prompt)
        return await self._generate_text(prompt)

    async def _draft_synthesis(
        self, formatted_inputs: str, reasoning: str, mode: str
    ) -> Optional[Dict[str, Any]]:
        """
        Step 2: Generate initial synthesis based on reasoning.

        Args:
            formatted_inputs: Formatted input contents
            reasoning: Reasoning trace from step 1
            mode: Synthesis mode (connect, inspire, debate)

        Returns:
            Draft synthesis as dict, or None if parsing fails
        """
        prompt_template = DRAFTING_PROMPTS.get(mode, DRAFTING_PROMPTS["connect"])
        prompt = prompt_template.format(reasoning=reasoning, inputs=formatted_inputs)
        prompt = self._truncate_content(prompt)

        response = await self._generate_text(prompt)
        return self._parse_response(response)

    async def _review_draft(self, formatted_inputs: str, draft: Dict[str, Any]) -> str:
        """
        Step 3: Self-critique the draft for quality.

        Args:
            formatted_inputs: Formatted input contents
            draft: Draft synthesis from step 2

        Returns:
            Critique as plain text
        """
        draft_str = json.dumps(draft, indent=2)
        prompt = REVIEW_PROMPT.format(draft=draft_str, inputs=formatted_inputs)
        prompt = self._truncate_content(prompt)
        return await self._generate_text(prompt)

    async def _refine_draft(self, draft: Dict[str, Any], critique: str) -> Optional[Dict[str, Any]]:
        """
        Step 4: Improve the draft based on critique.

        Args:
            draft: Draft synthesis from step 2
            critique: Critique from step 3

        Returns:
            Refined synthesis as dict, or None if parsing fails
        """
        draft_str = json.dumps(draft, indent=2)
        prompt = REFINEMENT_PROMPT.format(draft=draft_str, critique=critique)
        prompt = self._truncate_content(prompt)

        response = await self._generate_text(prompt)
        return self._parse_response(response)

    async def _generate_text(self, prompt: str) -> str:
        """Helper to generate text using chat interface."""
        # Clean up prompt indentation if needed, but usually prompt templates handle it.
        # Create a user message with the prompt
        messages = [
            ChatMessage(role="user", content=prompt),
        ]
        response = await self._llm.chat(messages)
        return response.content

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _format_inputs(self, contents: List[str]) -> str:
        """Format input contents for the prompt."""
        formatted = []
        for i, content in enumerate(contents, 1):
            # Truncate individual inputs if too long
            truncated = content[:5000] if len(content) > 5000 else content
            formatted.append(f"--- INPUT {i} ---\n{truncated}\n")
        return "\n".join(formatted)

    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse the LLM response as JSON."""
        try:
            # Try to extract JSON from the response (handle markdown code blocks)
            text = response.strip()
            if text.startswith("```"):
                # Remove code block markers
                lines = text.split("\n")
                # Find the end of the code block
                end_idx = len(lines) - 1
                for i, line in enumerate(lines[1:], 1):
                    if line.strip() == "```":
                        end_idx = i
                        break
                text = "\n".join(lines[1:end_idx])

            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"[SynthesisAgent] Failed to parse JSON: {e}")
            logger.debug(f"[SynthesisAgent] Raw response: {response[:500]}")
            return None

    def _format_node_content(self, synthesis_data: Dict[str, Any]) -> str:
        """Format synthesis data as Markdown content for the node."""
        parts = []

        if synthesis_data.get("main_insight"):
            parts.append(synthesis_data["main_insight"])
            parts.append("")

        if synthesis_data.get("recommendation"):
            parts.append(f"**Recommendation:** {synthesis_data['recommendation']}")

        if synthesis_data.get("key_risk"):
            parts.append(f"**Key Risk:** {synthesis_data['key_risk']}")

        themes = synthesis_data.get("supporting_themes", [])
        if themes:
            parts.append("")
            parts.append(f"*Themes: {', '.join(themes)}*")

        return "\n".join(parts)
