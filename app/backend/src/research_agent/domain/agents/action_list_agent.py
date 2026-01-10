"""Action List generation agent for Magic Cursor."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

from research_agent.domain.agents.base_agent import BaseOutputAgent, OutputEvent, OutputEventType
from research_agent.domain.entities.output import ActionItem, ActionListData, SourceRef
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.infrastructure.llm.prompts import PromptLoader
from research_agent.shared.utils.logger import logger

# Template paths
ACTION_LIST_SYSTEM_TEMPLATE = "agents/action_list/system.j2"
ACTION_LIST_GENERATION_TEMPLATE = "agents/action_list/generation.j2"


class ActionListAgent(BaseOutputAgent):
    """
    Agent for extracting action items from canvas node content.

    Used by Magic Cursor "Action List" action.

    Generation Strategy:
    1. Collect content from all selected canvas nodes
    2. Identify action items and tasks
    3. Categorize by priority
    4. Include source attribution
    """

    def __init__(
        self,
        llm_service: LLMService,
        max_tokens_per_request: int = 4000,
        skills: List[Any] = None,
    ):
        super().__init__(llm_service, max_tokens_per_request)
        self._skills = skills or []
        self._prompt_loader = PromptLoader.get_instance()

    @property
    def output_type(self) -> str:
        return "action_list"

    async def generate(
        self,
        document_content: str,
        document_title: Optional[str] = None,
        skills: List[Any] = None,
        **kwargs: Any,
    ) -> AsyncIterator[OutputEvent]:
        """
        Extract action items from node content.

        Args:
            document_content: Combined content from canvas nodes
            document_title: Optional title for the action list
            **kwargs:
                - node_data: List of {id, title, content} for source attribution
                - snapshot_context: Selection box coordinates for refresh

        Yields:
            OutputEvent instances as generation progresses
        """
        node_data: List[Dict[str, Any]] = kwargs.get("node_data", [])
        snapshot_context: Optional[Dict[str, Any]] = kwargs.get("snapshot_context")
        current_skills = skills if skills is not None else self._skills

        logger.info(
            f"[ActionListAgent] Starting action list extraction from {len(node_data)} nodes"
        )

        yield self._emit_started("Extracting action items...")

        try:
            # Format node content for the prompt
            node_content_str = self._format_node_content(node_data, document_content)

            # Truncate if necessary
            content = self._truncate_content(node_content_str)

            yield self._emit_progress(0.2, message="Analyzing content for tasks...")

            # Build prompt using Jinja2 templates
            user_prompt = self._prompt_loader.render(
                ACTION_LIST_GENERATION_TEMPLATE,
                node_content=content,
                skills=current_skills,
            )

            system_prompt = self._prompt_loader.render(
                ACTION_LIST_SYSTEM_TEMPLATE,
                skills=current_skills,
            )

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]

            yield self._emit_progress(0.4, message="Identifying action items...")

            # Generate action list
            logger.info("[ActionListAgent] Calling LLM for action list extraction")
            response = await self._llm.chat(messages)

            yield self._emit_progress(0.8, message="Processing action items...")

            # Parse response
            action_list_data = self._parse_action_list_response(response.content, snapshot_context)

            if action_list_data is None:
                raise ValueError("Failed to parse action list response from LLM")

            logger.info(f"[ActionListAgent] Extracted {len(action_list_data.items)} action items")

            # Emit complete with action list data
            yield OutputEvent(
                type=OutputEventType.GENERATION_COMPLETE,
                message="Action list extraction complete",
                node_data=action_list_data.to_dict(),
            )

        except Exception as e:
            logger.error(f"[ActionListAgent] Extraction failed: {e}", exc_info=True)
            yield self._emit_error(f"Action list extraction failed: {str(e)}")

    def _format_node_content(self, node_data: List[Dict[str, Any]], fallback_content: str) -> str:
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

    def _parse_action_list_response(
        self,
        response: str,
        snapshot_context: Optional[Dict[str, Any]],
    ) -> Optional[ActionListData]:
        """Parse the LLM response into ActionListData."""
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

            # Extract items
            items = []
            for item in data.get("items", []):
                items.append(
                    ActionItem(
                        id=item.get("id", str(uuid4())[:8]),
                        text=item.get("text", ""),
                        done=item.get("done", False),
                        priority=item.get("priority", "medium"),
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

            return ActionListData(
                title=data.get("title", "Action Items"),
                items=items,
                source_refs=source_refs,
                snapshot_context=snapshot_context,
            )

        except json.JSONDecodeError as e:
            logger.error(f"[ActionListAgent] JSON parse error: {e}")
            logger.debug(f"[ActionListAgent] Raw response: {response[:500]}...")

            # Return empty action list on parse failure
            return ActionListData(
                title="Action Items",
                items=[],
                source_refs=[],
                snapshot_context=snapshot_context,
            )

        except Exception as e:
            logger.error(f"[ActionListAgent] Parse error: {e}", exc_info=True)
            return None
