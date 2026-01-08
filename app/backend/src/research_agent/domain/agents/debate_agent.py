"""Debate generation agent using LangGraph workflow."""

import asyncio
import json
from typing import Any, AsyncIterator, Dict, List
from uuid import uuid4

from research_agent.domain.agents.base_agent import BaseOutputAgent, OutputEvent, OutputEventType
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.shared.utils.logger import logger

# Prompts
DEBATE_SYSTEM_PROMPT = """You are a skilled debater and critical thinker.
Your task is to analyze a thesis and generate arguments for (Pro) or against (Con) it.
You must be logical, evidence-based, and concise.

IMPORTANT: Respond with ONLY valid JSON."""

GENERATE_ARGUMENTS_PROMPT = """Analyze the following statement and generate {count} distinct {stance} arguments.

Statement: "{statement}"

Context:
{context}

Existing Arguments (to avoid):
{existing_arguments}

Generate {stance} arguments (supporting if Pro, opposing if Con).
Each argument should be a concise claim (1 sentence) followed by a brief reasoning (1-2 sentences).

Respond with a JSON object:
{{
  "arguments": [
    {{
      "label": "Short Claim (5-8 words)",
      "content": "Reasoning and evidence...",
      "type": "{stance}"
    }}
  ]
}}"""

class DebateAgent(BaseOutputAgent):
    """
    Agent for generating adversarial debate trees (Pro vs Con).
    """

    def __init__(
        self,
        llm_service: LLMService,
        max_tokens_per_request: int = 4000,
    ):
        super().__init__(llm_service, max_tokens_per_request)

    @property
    def output_type(self) -> str:
        return "debate"

    async def generate(
        self,
        document_content: str,
        document_title: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[OutputEvent]:
        """
        Generate a debate tree from a thesis (document_content).

        This simplifies the graph approach into a procedural generation for the MVP:
        1. Root (Thesis)
        2. Level 1: Generate 2-3 Con arguments (Counter-points)
        3. Level 2: Generate 1-2 Pro arguments (Rebuttals) for each Con
        """
        thesis = document_content
        context = kwargs.get("context", "")

        logger.info(f"[DebateAgent] Starting debate generation for: {thesis[:50]}...")
        yield self._emit_started("Starting debate generation")

        # 1. Create Root Node
        root_id = f"debate-root-{uuid4().hex[:8]}"
        root_node = {
            "id": root_id,
            "label": document_title or "Thesis",
            "content": thesis,
            "type": "thesis", # Visualizer will treat this as neutral/central
            "depth": 0
        }
        yield self._emit_node_added(root_id, root_node)

        # 2. Generate First Round: Counter-Arguments (Con)
        yield self._emit_progress(0.2, "Generating counter-arguments...")

        cons = await self._generate_arguments(
            statement=thesis,
            context=context,
            stance="Con",
            count=3,
            existing=[]
        )

        for con in cons:
            con_id = f"debate-node-{uuid4().hex[:8]}"
            con_node = {
                "id": con_id,
                "label": con["label"],
                "content": con["content"],
                "type": "con", # Red
                "depth": 1,
                "parent_id": root_id
            }
            yield self._emit_node_added(con_id, con_node)

            # Edge: Root -> Con (Contradicts)
            edge_id = f"edge-{uuid4().hex[:8]}"
            edge = {
                "id": edge_id,
                "source": root_id,
                "target": con_id,
                "relationType": "contradicts",
                "label": "challenges"
            }
            yield self._emit_edge_added(edge_id, edge)

            # 3. Generate Second Round: Rebuttals (Pro) for each Con
            # "Defend the thesis against this specific counter-argument"
            yield self._emit_progress(0.5, f"Rebutting: {con['label'][:20]}...")

            rebuttal_statement = f"Thesis: {thesis}\nCounter-Argument: {con['content']}"
            pros = await self._generate_arguments(
                statement=rebuttal_statement,
                context=context,
                stance="Pro",
                count=1, # One strong rebuttal per counter
                existing=[]
            )

            for pro in pros:
                pro_id = f"debate-node-{uuid4().hex[:8]}"
                pro_node = {
                    "id": pro_id,
                    "label": pro["label"],
                    "content": pro["content"],
                    "type": "pro", # Blue
                    "depth": 2,
                    "parent_id": con_id
                }
                yield self._emit_node_added(pro_id, pro_node)

                # Edge: Con -> Pro (Contradicts/Rebuts)
                rebuttal_edge_id = f"edge-{uuid4().hex[:8]}"
                rebuttal_edge = {
                    "id": rebuttal_edge_id,
                    "source": con_id,
                    "target": pro_id,
                    "relationType": "contradicts", # Or 'supports' the thesis? No, physically connected to Con, so it contradicts the Con.
                    "label": "rebuts"
                }
                yield self._emit_edge_added(rebuttal_edge_id, rebuttal_edge)

        yield self._emit_complete("Debate generation complete")

    async def _generate_arguments(
        self,
        statement: str,
        context: str,
        stance: str, # "Pro" or "Con"
        count: int,
        existing: List[str]
    ) -> List[Dict[str, str]]:
        """Helper to call LLM and parse arguments."""

        prompt = GENERATE_ARGUMENTS_PROMPT.format(
            statement=statement,
            context=context,
            stance=stance,
            count=count,
            existing_arguments=", ".join(existing) if existing else "None"
        )

        messages = [
            ChatMessage(role="system", content=DEBATE_SYSTEM_PROMPT),
            ChatMessage(role="user", content=prompt)
        ]

        try:
            response = await self._llm.chat(messages)
            content = response.content.strip()

            # Basic JSON extraction
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            data = json.loads(content.strip())
            return data.get("arguments", [])
        except Exception as e:
            logger.error(f"[DebateAgent] Failed to generate arguments: {e}")
            return []
