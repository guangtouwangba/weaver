"""Summary generation agent."""

import json
from typing import Any, AsyncIterator, Dict, Optional

from research_agent.domain.agents.base_agent import BaseOutputAgent, OutputEvent, OutputEventType
from research_agent.domain.entities.output import KeyFinding, SummaryData
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.shared.utils.logger import logger


# Prompts for summary generation
SUMMARY_SYSTEM_PROMPT = """You are an expert document analyst specializing in creating executive summaries.
Your task is to analyze documents and produce clear, actionable summaries with key findings.

IMPORTANT: You must respond with ONLY valid JSON, no other text or explanation.
"""

SUMMARY_GENERATION_PROMPT = """Analyze the following document and create an executive summary.

Document Title: {title}

Document Content:
{content}

Create a comprehensive yet concise executive summary that:
1. Captures the main theme and purpose of the document
2. Highlights the most important information
3. Identifies key findings with specific, actionable insights

Respond with a JSON object in this exact format:
{{
  "summary": "A comprehensive 2-3 paragraph executive summary of the document. Focus on the main themes, key arguments, and important conclusions. Write in clear, professional language.",
  "keyFindings": [
    {{
      "label": "Short category label (2-4 words, e.g., 'AI Adoption', 'Market Trends')",
      "content": "Specific finding or insight with relevant details or metrics"
    }},
    {{
      "label": "Another category label",
      "content": "Another specific finding"
    }}
  ]
}}

Guidelines:
- The summary should be 2-3 paragraphs, approximately 150-250 words
- Include 3-5 key findings
- Each key finding should have a brief label and a detailed content description
- Focus on actionable insights and concrete data when available
- Maintain a professional, analytical tone

Remember: Respond with ONLY the JSON object, nothing else."""


class SummaryAgent(BaseOutputAgent):
    """
    Agent for generating executive summaries from document content.

    Generation Strategy:
    1. Analyze document content
    2. Generate executive summary
    3. Extract key findings
    4. Return structured SummaryData

    Unlike MindmapAgent, this agent generates the complete output in a single pass.
    """

    def __init__(
        self,
        llm_service: LLMService,
        max_tokens_per_request: int = 4000,
    ):
        """
        Initialize the summary agent.

        Args:
            llm_service: LLM service for text generation
            max_tokens_per_request: Maximum tokens per LLM request
        """
        super().__init__(llm_service, max_tokens_per_request)

    @property
    def output_type(self) -> str:
        """Return the output type."""
        return "summary"

    async def generate(
        self,
        document_content: str,
        document_title: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[OutputEvent]:
        """
        Generate summary from document content.

        Args:
            document_content: Full document text
            document_title: Optional document title for context
            **kwargs: Additional parameters (unused)

        Yields:
            OutputEvent instances as generation progresses
        """
        title = document_title or "Document"
        logger.info(f"[SummaryAgent] Starting summary generation for: {title}")

        # Emit start event
        yield self._emit_started(f"Starting summary generation for: {title}")

        try:
            # Truncate content if necessary
            content = self._truncate_content(document_content)

            # Emit progress: preparing
            yield self._emit_progress(0.1, message="Analyzing document content...")

            # Build prompt
            user_prompt = SUMMARY_GENERATION_PROMPT.format(
                title=title,
                content=content,
            )

            messages = [
                ChatMessage(role="system", content=SUMMARY_SYSTEM_PROMPT),
                ChatMessage(role="user", content=user_prompt),
            ]

            # Emit progress: generating
            yield self._emit_progress(0.3, message="Generating executive summary...")

            # Generate summary
            logger.info("[SummaryAgent] Calling LLM for summary generation")
            response = await self._llm.chat(messages)

            # Emit progress: parsing
            yield self._emit_progress(0.8, message="Processing summary...")

            # Parse JSON response
            summary_data = self._parse_summary_response(response.content, title)

            if summary_data is None:
                raise ValueError("Failed to parse summary response from LLM")

            logger.info(
                f"[SummaryAgent] Generated summary with {len(summary_data.key_findings)} key findings"
            )

            # Emit complete with summary data
            yield OutputEvent(
                type=OutputEventType.GENERATION_COMPLETE,
                message="Summary generation complete",
                node_data=summary_data.to_dict(),  # Use node_data to carry the result
            )

        except Exception as e:
            logger.error(f"[SummaryAgent] Generation failed: {e}", exc_info=True)
            yield self._emit_error(f"Summary generation failed: {str(e)}")

    def _parse_summary_response(
        self,
        response: str,
        document_title: str,
    ) -> Optional[SummaryData]:
        """
        Parse the LLM response into SummaryData.

        Args:
            response: Raw LLM response text
            document_title: Document title for the summary

        Returns:
            SummaryData if parsing successful, None otherwise
        """
        try:
            # Try to extract JSON from response
            response_text = response.strip()

            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                # Remove markdown code block markers
                lines = response_text.split("\n")
                # Skip first line (```json) and last line (```)
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

            # Extract key findings
            key_findings = []
            for kf in data.get("keyFindings", []):
                key_findings.append(
                    KeyFinding(
                        label=kf.get("label", "Finding"),
                        content=kf.get("content", ""),
                    )
                )

            return SummaryData(
                summary=data.get("summary", ""),
                key_findings=key_findings,
                document_title=document_title,
            )

        except json.JSONDecodeError as e:
            logger.error(f"[SummaryAgent] JSON parse error: {e}")
            logger.debug(f"[SummaryAgent] Raw response: {response[:500]}...")

            # Fallback: try to extract summary from plain text
            if len(response) > 100:
                return SummaryData(
                    summary=response[:1000],
                    key_findings=[
                        KeyFinding(
                            label="Note",
                            content="Summary was generated but could not be properly formatted.",
                        )
                    ],
                    document_title=document_title,
                )

            return None

        except Exception as e:
            logger.error(f"[SummaryAgent] Parse error: {e}", exc_info=True)
            return None


