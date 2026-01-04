# Proposal: Optimize Synthesis Agent with Reasoning & Review

## Why
The current synthesis agent uses a single-pass generation approach which often leads to shallow insights. Complex syntheses (e.g., connecting "Geography" and "Physics") require deeply understanding domain relationships and verifying the logic. The user specifically requested an agent that "thinks," "reviews," and understands "connections/links" between nodes.

## What Changes
We will upgrade the `SynthesisAgent` to use a multi-step reasoning workflow:
1.  **Reasoning Phase**: Analyze relationship and plan the synthesis angle (Chain-of-Thought).
2.  **Drafting Phase**: Generate the initial insight.
3.  **Review Phase**: Critique the draft for logical soundness, domain accuracy, and depth.
4.  **Refinement Phase**: Produce the final high-quality insight.

This connects to the "Thinking" concepts we've introduced elsewhere, ensuring the agent provides valuable, non-obvious connections.

## Owner
@siqiuchen

## Impact
- **Backend**: `SynthesisAgent` in `research_agent/domain/agents` will be significantly refactored.
- **Frontend**: The `SynthesisResultCard` (now a canvas node) will likely need to show "Thinking..." status or intermediate steps if we choose to expose them (optional, but good for UX).
