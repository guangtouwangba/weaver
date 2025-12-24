"""
Verification script for Intelligent Canvas features.
Run this script to test Clustering, Linking, and Report Generation logic.
"""

import asyncio
import os

# Import entities and services
# We need to set up python path to include app/backend/src
# Import entities and services
# We need to set up python path to include app/backend/src
import sys
import uuid
from datetime import datetime
from typing import List
from unittest.mock import MagicMock

# Mock asyncpg to avoid DB client imports failure
sys.modules["asyncpg"] = MagicMock()
# Mock supabase
sys.modules["supabase"] = MagicMock()
# Mock cryptography
sys.modules["cryptography"] = MagicMock()
sys.modules["cryptography.fernet"] = MagicMock()

sys.path.append(os.path.join(os.getcwd(), "app/backend/src"))

from research_agent.domain.entities.canvas import CanvasEdge, CanvasNode, CanvasSection
from research_agent.domain.services.canvas_narrative_service import (
    CanvasNarrativeService,
)
from research_agent.domain.services.canvas_structure_service import (
    CanvasStructureService,
)
from research_agent.infrastructure.embedding.base import EmbeddingService
from research_agent.infrastructure.llm.base import ChatMessage, ChatResponse, LLMService

# --- Mocks ---


class MockEmbeddingService(EmbeddingService):
    async def embed(self, text: str) -> List[float]:
        # Simple deterministic embedding based on length or hash to allow testing clustering
        # We simulate 2 clusters by mapping text to 2 different vector spaces
        if "ClusterA" in text:
            return [1.0, 0.0, 0.0]
        elif "ClusterB" in text:
            return [0.0, 1.0, 0.0]
        return [0.5, 0.5, 0.0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed(t) for t in texts]


class MockLLMService(LLMService):
    async def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        content = messages[-1].content
        response_content = "Mock Response"
        if "Summarize the common theme" in content:
            response_content = "Test Cluster Title"
        elif (
            "Classify the relationship" in content or "source_type" in content
        ):  # Prompt template check
            # Return valid JSON for edge classification
            response_content = '{"relation_type": "supports", "label": "supports"}'
        elif "Report:" in content:
            response_content = "Generated Report Content: Based on the nodes..."

        return ChatResponse(
            content=response_content,
            model="mock",
            usage={"prompt_tokens": 10, "completion_tokens": 10},
            cost=0.0,
        )

    async def chat_stream(self, messages: List[ChatMessage]):
        yield "Mock stream"


# --- Tests ---


async def test_auto_structure():
    print("--- Testing Auto-Structuring ---")

    # 1. Setup Data
    nodes = [
        CanvasNode(id="1", title="A1", content="ClusterA Note 1", x=0, y=0),
        CanvasNode(id="2", title="A2", content="ClusterA Note 2", x=0, y=0),
        CanvasNode(id="3", title="B1", content="ClusterB Note 1", x=0, y=0),
        CanvasNode(id="4", title="B2", content="ClusterB Note 2", x=0, y=0),
        CanvasNode(id="5", title="C1", content="Ambiguous Note", x=0, y=0),
    ]

    # 2. Init Service
    embed_service = MockEmbeddingService()
    llm_service = MockLLMService()
    service = CanvasStructureService(embed_service, llm_service)

    # 3. Test Clustering
    print("Running Cluster Nodes...")
    sections = await service.cluster_nodes(nodes, similarity_threshold=0.9)

    print(f"Created {len(sections)} sections.")
    for s in sections:
        print(f"Section '{s.title}': {s.node_ids}")

    # Assert
    # We expect 2 clusters (A and B). Node 5 might be singleton or merged?
    # Our greedy leader logic:
    # A1(1,0,0) -> Leader. A2(1,0,0) -> Joins A1.
    # B1(0,1,0) -> New Leader. B2(0,1,0) -> Joins B1.
    # C1(0.5,0.5,0) -> Dist(A1)=0.707 (sim). Threshold 0.9.
    # So C1 should be separate.
    # But currently we filter out singletons in the service (len < 2).
    # So we expect 2 sections.
    assert len(sections) == 2
    assert "Test Cluster Title" in sections[0].title

    # 4. Test Linking
    print("Running Suggest Links...")
    edges = await service.suggest_global_links(nodes, [], similarity_threshold=0.5)
    # Use lower threshold to force check C1 against others.
    # A1 & A2 match perfectly -> but they are in same cluster (should we link intra-cluster? Yes).
    # Service logic checks all pairs.

    print(f"Suggested {len(edges)} edges.")
    # With N=5, pairs = 10.
    # A1-A2 (sim 1.0) -> Pass threshold -> Call LLM -> Returns "supports" -> Link.
    # A1-B1 (sim 0.0) -> Fail threshold.
    # A1-C1 (sim 0.707) -> Pass 0.5 threshold -> Call LLM -> Link.

    assert len(edges) > 0

    print("✅ Auto-Structure Test Passed")


async def test_narrative_generation():
    print("\n--- Testing Narrative Generation ---")

    # 1. Setup Graph
    # A -> B -> C
    n1 = CanvasNode(id="1", title="Concept A", content="Start", y=0)
    n2 = CanvasNode(id="2", title="Concept B", content="Middle", y=100)
    n3 = CanvasNode(id="3", title="Concept C", content="End", y=200)

    nodes = [n3, n1, n2]  # Shuffled input
    edges = [CanvasEdge(source="1", target="2"), CanvasEdge(source="2", target="3")]

    # 2. Init Service
    llm_service = MockLLMService()
    service = CanvasNarrativeService(llm_service)

    # 3. Test Path Planning
    print("Planning Path...")
    ordered = service.plan_narrative_path(nodes, edges)

    print(f"Order: {[n.title for n in ordered]}")
    # Expected: Concept A -> Concept B -> Concept C
    assert ordered[0].id == "1"
    assert ordered[1].id == "2"
    assert ordered[2].id == "3"

    # 4. Test Report Generation
    print("Generating Report...")
    report = await service.generate_report(ordered, edges)
    print(f"Report: {report}")

    assert "Generated Report Content" in report
    print("✅ Narrative Generation Test Passed")


async def main():
    await test_auto_structure()
    await test_narrative_generation()


if __name__ == "__main__":
    asyncio.run(main())
