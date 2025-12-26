# Change: Refactor Mindmap Agent to LangGraph Architecture

## Why
The current MindmapAgent uses a procedural async generator pattern that mixes control flow with LLM calls. Refactoring to LangGraph provides:
- **Clear separation**: Each step (analyze → generate root → expand branches) is a distinct node
- **State management**: TypedDict state makes data flow explicit and debuggable
- **Extensibility**: Easy to add conditional edges, retry logic, or parallel processing
- **Consistency**: Aligns with the existing RAG pipeline which already uses LangGraph

## What Changes
- **LangGraph Workflow**: Replace procedural `generate()` with a `StateGraph` workflow
- **Streaming Integration**: Emit `OutputEvent` from graph nodes to maintain real-time display
- **State Schema**: Define `MindmapState` TypedDict for explicit state tracking
- **Preserve Capabilities**:
  - Keep JSON node/edge output format for interactive canvas
  - Keep `explain_node()` and `expand_node()` for post-generation editing
  - Keep level-by-level streaming for real-time UX

## Impact
- **Specs**: `agents` capability will be updated with LangGraph-based mindmap generation
- **Code**:
  - New `app/backend/src/research_agent/application/graphs/mindmap_graph.py` - LangGraph workflow
  - Refactor `mindmap_agent.py` to use the graph internally
  - Preserve `BaseOutputAgent` interface for backward compatibility

