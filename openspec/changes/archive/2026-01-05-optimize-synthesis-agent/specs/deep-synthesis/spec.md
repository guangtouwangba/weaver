# Capability: Deep Synthesis Agent

## ADDED Requirements

### Requirement: Multi-step Reasoning Workflow
The agent MUST use a multi-stage process to generate synthesis, ensuring depth and accuracy.

#### Scenario: Multi-step Reasoning
Given the `SynthesisAgent` is invoked with multiple source nodes
When it begins processing
Then it must first generate a reasoning trace identifying domains and connections between sources
And emit a "Thinking..." progress event
And continue processing to the final insight.

#### Scenario: Self-Review
Given a draft insight is generated
When the agent proceeds to the review phase
Then it must critique the draft for accuracy and logical soundness
And apply these critiques to refine the final output
And emit a "Reviewing..." progress event.

### Requirement: Domain-Aware Analysis
The agent MUST explicitly identify and leverage domain knowledge.

#### Scenario: Domain Awareness
Given the inputs contain content from specific fields (e.g. Physics, History)
When reasoning occurs
Then the agent must explicitly identify these domains in the reasoning step
And use this context to find inter-disciplinary links.
