"""
Canvas Narrative Service - Transforms canvas graph into linear narrative.

This service acts as the "Writer" for the canvas, planning a logical path through
the knowledge graph and generating coherent reports.
"""

from typing import Dict, List, Optional, Set

from research_agent.domain.entities.canvas import CanvasEdge, CanvasNode
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.shared.utils.logger import logger


class CanvasNarrativeService:
    """Service to generate narrative from canvas."""

    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service

    def plan_narrative_path(
        self,
        nodes: List[CanvasNode],
        edges: List[CanvasEdge],
    ) -> List[CanvasNode]:
        """
        Plan a reading order for the nodes using topological sort.
        Handles cycles by tracking visited nodes.
        """
        if not nodes:
            return []

        # 1. Build Adjacency List & In-Degree
        adj: Dict[str, List[str]] = {n.id: [] for n in nodes}
        in_degree: Dict[str, int] = {n.id: 0 for n in nodes}
        node_map = {n.id: n for n in nodes}

        # Only consider edges between selected nodes
        valid_node_ids = set(node_map.keys())

        for edge in edges:
            if edge.source in valid_node_ids and edge.target in valid_node_ids:
                adj[edge.source].append(edge.target)
                in_degree[edge.target] += 1

        # 2. Kahn's Algorithm for Topological Sort
        queue = [nid for nid in valid_node_ids if in_degree[nid] == 0]

        # Sort roots to have deterministic start (e.g. by title or y-position)
        # Top-down reading (y position) is a good heuristic for unconnected roots
        queue.sort(key=lambda nid: node_map[nid].y)

        ordered_ids = []

        while queue:
            u = queue.pop(0)
            ordered_ids.append(u)

            # Sort neighbors for deterministic flow
            neighbors = adj[u]
            neighbors.sort(key=lambda nid: node_map[nid].y)

            for v in neighbors:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # 3. Handle Cycles / Disconnected Components
        # If ordered_ids doesn't contain all nodes, there are cycles or disconnected islands remained
        if len(ordered_ids) < len(nodes):
            remaining = [nid for nid in valid_node_ids if nid not in ordered_ids]
            # Simple fallback: Sort remaining by Y position and append
            remaining.sort(key=lambda nid: node_map[nid].y)
            ordered_ids.extend(remaining)

        return [node_map[nid] for nid in ordered_ids]

    async def generate_report(
        self,
        ordered_nodes: List[CanvasNode],
        edges: List[CanvasEdge],
        prompt_instruction: str = "Write a comprehensive summary report based on these notes.",
    ) -> str:
        """
        Generate a text report based on the ordered nodes and their relationships.
        """
        if not ordered_nodes:
            return "No content selected."

        # 1. Build context string with explicit relationships
        context_parts = []
        node_map = {n.id: n for n in ordered_nodes}
        valid_ids = set(node_map.keys())

        # Build edge lookup
        # source -> [(target, relation_label?)]
        # Since CanvasEdge is minimal, we assume simple connection or check `label` if added later.
        # For now, just "connected to".
        connections: Dict[str, List[str]] = {n.id: [] for n in ordered_nodes}
        for edge in edges:
            if edge.source in valid_ids and edge.target in valid_ids:
                target_title = node_map[edge.target].title
                connections[edge.source].append(f"-> leads to '{target_title}'")

        for i, node in enumerate(ordered_nodes, 1):
            relations_str = ""
            if connections[node.id]:
                relations_str = f"   (Relations: {', '.join(connections[node.id])})"

            part = f"""
            Node {i}: {node.title} ({node.type})
            Content: {node.content}
            {relations_str}
            """
            context_parts.append(part)

        full_context = "\n".join(context_parts)

        # 2. Construct Prompt
        system_prompt = """You are a research assistant writing a structured report.
        Use the provided research notes to write a coherent, flowy narrative.
        Follow the logical order of the notes.
        Explicitly reference specific points.
        Resolve any contradictions mentioned in the notes.
        """

        user_prompt = f"""
        {prompt_instruction}
        
        Here are the research notes in logical order:
        {full_context}
        
        Report:
        """

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]

        try:
            response = await self._llm_service.chat(messages)
            return response.content
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return f"Error generating report: {e}"
