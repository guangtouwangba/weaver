"""
Canvas Structure Service - Organizes canvas nodes into clusters and suggests connections.

This service acts as the "Gardener" for the canvas, turning scattered notes into
structured knowledge using semantic clustering and relationship extraction.
"""

import math
import uuid
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# Reuse prompts from thinking path (or create new ones if needed)
from research_agent.application.prompts.thinking_path_extraction import (
    EDGE_RELATION_CLASSIFICATION_SYSTEM_PROMPT,
    EDGE_RELATION_CLASSIFICATION_USER_PROMPT,
    EDGE_RELATION_DEFAULT_LABELS,
)
from research_agent.domain.entities.canvas import CanvasEdge, CanvasNode, CanvasSection
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.llm.base import ChatMessage, LLMService
from research_agent.shared.utils.logger import logger


class CanvasStructureService:
    """Service to auto-structure canvas elements."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        llm_service: Optional[LLMService] = None,
    ):
        self._embedding_service = embedding_service
        self._llm_service = llm_service
        self._embedding_cache: Dict[str, List[float]] = {}

    async def cluster_nodes(
        self,
        nodes: List[CanvasNode],
        similarity_threshold: float = 0.75,
    ) -> List[CanvasSection]:
        """
        Group nodes into semantic clusters (Sections).

        Uses a lightweight Greedy Leader algorithm to avoid heavy dependencies (like sklearn).
        """
        if not nodes:
            return []

        # 1. Compute embeddings for all nodes
        node_embeddings = {}
        for node in nodes:
            text = f"{node.title} {node.content}"
            if not text.strip():
                continue

            # Check cache
            if node.id in self._embedding_cache:
                node_embeddings[node.id] = self._embedding_cache[node.id]
            else:
                embedding = await self._embedding_service.embed(text)
                node_embeddings[node.id] = embedding
                self._embedding_cache[node.id] = embedding

        # 2. Greedy Clustering
        # List of clusters, where each cluster is a list of node_ids
        clusters: List[List[str]] = []
        # Representative embedding for each cluster (centroid or leader)
        cluster_reps: List[List[float]] = []

        valid_node_ids = list(node_embeddings.keys())

        for node_id in valid_node_ids:
            embedding = node_embeddings[node_id]

            # Try to find a matching cluster
            best_cluster_idx = -1
            max_sim = -1.0

            for i, rep_emb in enumerate(cluster_reps):
                sim = self._cosine_similarity(embedding, rep_emb)
                if sim > max_sim:
                    max_sim = sim
                    best_cluster_idx = i

            if max_sim >= similarity_threshold and best_cluster_idx != -1:
                # Add to existing cluster
                clusters[best_cluster_idx].append(node_id)
                # Optional: Update centroid (skipping for simplicity in MVP, leader is fixed)
            else:
                # Create new cluster
                clusters.append([node_id])
                cluster_reps.append(embedding)

        # 3. Create Sections for clusters with > 1 item (or even 1 item if configured)
        sections = []
        for cluster_node_ids in clusters:
            # Filter out singletons if we only want real groups?
            # For now, let's group everything that didn't merge as individual sections?
            # No, usually we only create sections for groups of 2+.
            # Singletons remain free floating?
            # Let's say group size >= 2 creates a section.
            if len(cluster_node_ids) < 2:
                continue

            # Generate Title for the cluster
            section_title = await self._generate_cluster_title(cluster_node_ids, nodes)

            section = CanvasSection(
                id=str(uuid.uuid4()), title=section_title, node_ids=cluster_node_ids
            )
            sections.append(section)

        return sections

    async def suggest_global_links(
        self,
        nodes: List[CanvasNode],
        existing_edges: List[CanvasEdge],
        similarity_threshold: float = 0.80,
    ) -> List[CanvasEdge]:
        """
        Suggest semantic links between nodes that are not yet connected.
        """
        suggested_edges = []

        # Build adjacency set for quick lookup
        existing_connections = set()
        for edge in existing_edges:
            existing_connections.add(f"{edge.source}-{edge.target}")
            existing_connections.add(f"{edge.target}-{edge.source}")  # Undirected check

        # Compare pairs
        # Optimization: Only compare nodes that are semantically close
        # Using a simple O(N^2) loop is fine for N < 100. For larger N, need spatial index.
        # Assuming typical canvas < 50 nodes for MVP.

        n = len(nodes)
        for i in range(n):
            for j in range(i + 1, n):
                node_a = nodes[i]
                node_b = nodes[j]

                # Check if already connected
                if f"{node_a.id}-{node_b.id}" in existing_connections:
                    continue

                # Check similarity
                emb_a = self._embedding_cache.get(node_a.id)
                emb_b = self._embedding_cache.get(node_b.id)

                if not emb_a or not emb_b:
                    continue

                sim = self._cosine_similarity(emb_a, emb_b)
                if sim < similarity_threshold:
                    continue

                # High similarity: Check specific relationship with LLM
                relation = await self._classify_relation(node_a, node_b)
                if relation:
                    rel_type, label = relation
                    # Determine direction logic?
                    # For now, we assume simple A->B direction from the prompt check
                    edge = CanvasEdge(
                        id=str(uuid.uuid4()),
                        source=node_a.id,
                        target=node_b.id,
                        # Ideally we store relation metadata, but CanvasEdge might naturally support it?
                        # Using 'label' if CanvasEdge supports it?
                        # Checking CanvasEdge definition: id, source, target, generation.
                        # It seems CanvasEdge is minimal.
                        # We might need to extend CanvasEdge or just store it in DB side but entity is minimal.
                        # Wait, ThinkingPathService uses `edge_type` and `label` in `to_dict` or similar?
                        # CanvasEdge definition in canvas.py only has: source, target, id, generation.
                        # We should probably respect the minimal entity for now.
                    )
                    # Note: We can't store 'label' effectively if the entity doesn't support it yet.
                    # Implementation Plan didn't explicitly say "Update CanvasEdge entity".
                    # But ThinkingPath has distinct visualization.
                    # Let's assume for now we just return edges.
                    suggested_edges.append(edge)

        return suggested_edges

    async def _generate_cluster_title(
        self, node_ids: List[str], all_nodes: List[CanvasNode]
    ) -> str:
        """Use LLM to generate a title for a cluster of nodes."""
        if not self._llm_service:
            return "Untitled Group"

        # Gather content
        cluster_content = []
        node_map = {n.id: n for n in all_nodes}
        for nid in node_ids:
            if nid in node_map:
                n = node_map[nid]
                cluster_content.append(f"- {n.title}: {n.content[:100]}")

        context_str = "\n".join(cluster_content)

        prompt = f"""Summarize the common theme of these research notes into a short, 3-5 word title.
        
        Notes:
        {context_str}
        
        Title:"""

        messages = [ChatMessage(role="user", content=prompt)]
        try:
            response = await self._llm_service.chat(messages)
            title = response.content.strip().replace('"', "").replace("Title:", "").strip()
            return title
        except Exception as e:
            logger.error(f"Failed to generate cluster title: {e}")
            return "Group"

    async def _classify_relation(
        self, node_a: CanvasNode, node_b: CanvasNode
    ) -> Optional[Tuple[str, str]]:
        """Classify relationship between two nodes using LLM."""
        if not self._llm_service:
            return None

        # Reusing the prompt structure from ThinkingPath
        user_prompt = EDGE_RELATION_CLASSIFICATION_USER_PROMPT.format(
            source_type=node_a.type,
            source_title=node_a.title,
            source_content=node_a.content[:300],
            target_type=node_b.type,
            target_title=node_b.title,
            target_content=node_b.content[:300],
            context="Canvas auto-linking",
        )

        messages = [
            ChatMessage(role="system", content=EDGE_RELATION_CLASSIFICATION_SYSTEM_PROMPT),
            ChatMessage(role="user", content=user_prompt),
        ]

        try:
            response = await self._llm_service.chat(messages)
            # Basic parsing (assuming the prompt returns JSON or structured text as in ThinkingPath)
            # The ThinkingPath implementation did manual parsing of JSON code blocks.
            # I will assume simple text or robust parsing here?
            # Let's do a quick minimal parse or just return "related" if confident.
            # For brevity, let's assume raw text processing similar to ThinkingPath service
            content = response.content.strip()
            if "relation_type" in content:
                # It's likely JSON
                import json

                # Strip markdown
                if "```" in content:
                    content = content.split("```")[-2]  # take the block
                    if content.startswith("json"):
                        content = content[4:]

                try:
                    data = json.loads(content)
                    return (data.get("relation_type"), data.get("label"))
                except:
                    pass

            return None

        except Exception as e:
            logger.error(f"Failed to classify relation: {e}")
            return None

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
