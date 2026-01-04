"""Agent for synthesizing multiple content sources into consolidated insights."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

from research_agent.domain.agents.base_agent import BaseOutputAgent, OutputEvent, OutputEventType
from research_agent.infrastructure.llm.base import LLMService
from research_agent.shared.utils.logger import logger

PROMPTS = {
    "connect": """You are an expert analyst. Your task is to analyze these inputs and identify **hidden connections** and **common themes**.

Your goal is to find structural similarities, shared principles, or latent links between these seemingly distinct items.

Output ONLY a valid JSON object with this structure:
{
    "title": "A title highlighting the connection (e.g., 'The Link between X and Y')",
    "main_insight": "The core connection or shared theme found (2-3 sentences)",
    "recommendation": "How to leverage this connection",
    "key_risk": "Potential misinterpretations or false equivalences",
    "supporting_themes": ["shared theme 1", "shared theme 2"],
    "confidence": "high" | "medium" | "low"
}

Here are the inputs to connect:

{inputs}
""",
    "inspire": """You are a creative muse. Your task is to use the first input (or the collection of inputs) as a **lens** to reframe or re-imagine the others.

Your goal is to generate a **creative leap** or a **new perspective**. How does one idea change the meaning of the other?

Output ONLY a valid JSON object with this structure:
{
    "title": "An inspiring title (e.g., 'Reframing X through Y')",
    "main_insight": "The new perspective or creative leap generated (2-3 sentences)",
    "recommendation": "A creative direction to explore",
    "key_risk": "Feasibility or practicality concerns",
    "supporting_themes": ["new perspective 1", "new perspective 2"],
    "confidence": "high" | "medium" | "low"
}

Here are the inputs to mix:

{inputs}
""",
    "debate": """You are a critical thinker. Your task is to treat these inputs as **opposing or complementary arguments**.

Your goal is to identify **conflicts**, **tensions**, and **trade-offs**. Where do they disagree? Which argument is more robust in which context?

Output ONLY a valid JSON object with this structure:
{
    "title": "A provocative title (e.g., 'X vs Y: The Tension')",
    "main_insight": "The core conflict or tension identified (2-3 sentences)",
    "recommendation": "How to resolve or navigate this tension",
    "key_risk": "Biases or overlooked nuances",
    "supporting_themes": ["tension 1", "disagreement 2"],
    "confidence": "high" | "medium" | "low"
}

Here are the inputs to debate:

{inputs}
""",
}


class SynthesisAgent(BaseOutputAgent):
    """
    Agent for synthesizing multiple content sources into consolidated insights.

    This agent takes multiple pieces of content and generates a structured
    synthesis that identifies common themes, new insights, recommendations,
    and risks.
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
            f"[SynthesisAgent] Starting synthesis of {len(input_contents)} inputs with mode={mode}"
        )
        yield self._emit_started(f"Synthesizing {len(input_contents)} sources ({mode})")

        try:
            # Format inputs for the prompt
            formatted_inputs = self._format_inputs(input_contents)

            # Select prompt based on mode
            prompt_template = PROMPTS.get(mode, PROMPTS["connect"])
            prompt = prompt_template.format(inputs=formatted_inputs)

            # Truncate if needed
            prompt = self._truncate_content(prompt)

            yield self._emit_progress(0.3, message="Analyzing inputs...")

            # Call LLM
            response = await self._llm.generate(prompt)

            yield self._emit_progress(0.7, message="Generating synthesis...")

            # Parse response
            synthesis_data = self._parse_response(response)

            if synthesis_data is None:
                yield self._emit_error("Failed to parse synthesis response")
                return

            # Create a node for the synthesis result
            node_id = f"synthesis-{uuid4().hex[:8]}"
            node_data = {
                "id": node_id,
                "label": synthesis_data.get("title", "Consolidated Insight"),
                "content": self._format_node_content(synthesis_data),
                "type": "synthesis",
                "metadata": {
                    "source_node_ids": source_ids or [],
                    "synthesis_mode": mode,
                    "confidence": synthesis_data.get("confidence", "medium"),
                    "themes": synthesis_data.get("supporting_themes", []),
                },
                "status": "complete",
            }

            yield self._emit_node_added(node_id, node_data)
            yield self._emit_progress(1.0, message="Synthesis complete")

            # Emit complete with the synthesis data for storage
            yield OutputEvent(
                type=OutputEventType.GENERATION_COMPLETE,
                message=f"Synthesized {len(input_contents)} sources",
                node_data=synthesis_data,
            )

            logger.info(
                f"[SynthesisAgent] Synthesis complete: {synthesis_data.get('title', 'N/A')}"
            )

        except Exception as e:
            logger.error(f"[SynthesisAgent] Synthesis failed: {e}", exc_info=True)
            yield self._emit_error(str(e))

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
                text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

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
