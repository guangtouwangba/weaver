"""Unit tests for the SynthesisAgent multi-step reasoning pipeline."""

import json
from unittest.mock import MagicMock

import pytest
from research_agent.domain.agents.base_agent import OutputEventType
from research_agent.domain.agents.synthesis_agent import SynthesisAgent
from research_agent.infrastructure.llm.base import ChatResponse


class TestSynthesisAgent:
    """Test suite for SynthesisAgent with mocked LLM."""

    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service that returns predictable responses."""
        mock = MagicMock()

        # Track call count to return different responses for each step
        call_count = 0

        async def mock_chat(messages):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # Step 1: Reasoning
                content = """## Domain Analysis
- Input 1: Chemistry (Hydrogen)
- Input 2: Physics (Fire/Combustion)

## Potential Bridges
1. Chemical Reactions: Both relate to energy transformation
2. Elemental Science: Both involve atomic/molecular behavior
3. Energy Release: Both concepts involve release of stored energy

## Recommended Angle
Based on my analysis, the strongest bridge is Chemical Reactions because both hydrogen and fire are fundamentally about energy transformation through chemical bonds."""

            elif call_count == 2:
                # Step 2: Drafting
                content = json.dumps(
                    {
                        "title": "The Energy Dance: Hydrogen and Fire",
                        "main_insight": "Hydrogen and fire are intrinsically linked through combustion chemistry. Hydrogen serves as one of the most energy-dense fuels, and when it reacts with oxygen (fire), it releases tremendous energy. This connection represents the fundamental principle of energy transformation.",
                        "recommendation": "Explore hydrogen fuel cells as clean energy alternatives that harness this fundamental connection.",
                        "key_risk": "Oversimplifying the complex chemistry involved in combustion reactions.",
                        "supporting_themes": [
                            "energy transformation",
                            "combustion chemistry",
                            "clean energy",
                        ],
                        "confidence": "high",
                    }
                )

            elif call_count == 3:
                # Step 3: Review
                content = """## Critique
- Logical Soundness: 5 - The connection is scientifically accurate
- Accuracy: 4 - The science is correct but could be more detailed
- Depth: 4 - Good insight but could explore more applications
- Actionability: 4 - Recommendation is useful but generic

## Specific Issues
- Could mention water as the byproduct of hydrogen combustion

## Suggested Improvements
- Add mention of the clean energy aspect (water output)
- Include specific applications beyond fuel cells"""

            else:
                # Step 4: Refinement
                content = json.dumps(
                    {
                        "title": "The Energy Dance: Hydrogen and Fire - A Clean Energy Future",
                        "main_insight": "Hydrogen and fire share a profound connection through combustion chemistry. When hydrogen burns (reacts with oxygen), it releases energy while producing only water as a byproduct. This clean combustion makes hydrogen a promising candidate for sustainable energy, representing nature's elegant solution to energy transformation.",
                        "recommendation": "Invest in hydrogen fuel cell technology and green hydrogen production to harness this clean combustion for transportation and industrial applications.",
                        "key_risk": "Current hydrogen production methods often rely on fossil fuels, potentially negating environmental benefits without green hydrogen infrastructure.",
                        "supporting_themes": [
                            "clean combustion",
                            "sustainable energy",
                            "water byproduct",
                            "fuel cell technology",
                        ],
                        "confidence": "high",
                    }
                )

            return ChatResponse(content=content, model="mock", usage={})

        mock.chat = mock_chat
        return mock

    @pytest.fixture
    def agent(self, mock_llm_service):
        """Create a SynthesisAgent with mocked LLM."""
        return SynthesisAgent(llm_service=mock_llm_service)

    @pytest.mark.asyncio
    async def test_synthesize_calls_all_four_steps(self, agent):
        """Test that synthesize calls all 4 pipeline steps."""
        inputs = [
            "Hydrogen is the lightest element. It can be used as fuel.",
            "Fire is the rapid oxidation of a material. It releases heat and light.",
        ]

        events = []
        async for event in agent.synthesize(inputs, mode="connect"):
            events.append(event)

        # Should have: started, 4 progress events, node_added, progress(1.0), complete
        event_types = [e.type for e in events]

        assert OutputEventType.GENERATION_STARTED in event_types
        assert OutputEventType.NODE_ADDED in event_types
        assert OutputEventType.GENERATION_COMPLETE in event_types

        # Check progress messages indicate multi-step process
        progress_messages = [
            e.message for e in events if e.type == OutputEventType.GENERATION_PROGRESS
        ]
        assert any("Thinking" in m for m in progress_messages), "Should have thinking step"
        assert any("Drafting" in m for m in progress_messages), "Should have drafting step"
        assert any("Reviewing" in m for m in progress_messages), "Should have review step"
        assert any("Refining" in m for m in progress_messages), "Should have refine step"

    @pytest.mark.asyncio
    async def test_synthesize_returns_refined_content(self, agent):
        """Test that final output includes refined content."""
        inputs = ["Hydrogen is the lightest element.", "Fire is combustion."]

        node_event = None
        async for event in agent.synthesize(inputs, mode="connect"):
            if event.type == OutputEventType.NODE_ADDED:
                node_event = event

        assert node_event is not None
        assert node_event.node_data is not None

        # Check that refined content is used (has water byproduct mention from refinement)
        content = node_event.node_data.get("content", "")
        assert "water" in content.lower() or "clean" in content.lower()

        # Check metadata indicates deep synthesis was used
        metadata = node_event.node_data.get("metadata", {})
        assert metadata.get("reasoning_used") is True

    @pytest.mark.asyncio
    async def test_synthesize_requires_two_inputs(self, agent):
        """Test that synthesis fails with less than 2 inputs."""
        inputs = ["Only one input"]

        events = []
        async for event in agent.synthesize(inputs, mode="connect"):
            events.append(event)

        error_events = [e for e in events if e.type == OutputEventType.GENERATION_ERROR]
        assert len(error_events) == 1
        assert error_events[0].error_message is not None
        assert "2 inputs" in error_events[0].error_message
