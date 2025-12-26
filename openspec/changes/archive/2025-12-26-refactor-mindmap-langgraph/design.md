# Design: LangGraph-based Mindmap Agent

## Context
The current `MindmapAgent` uses nested async generators with manual control flow. The project already uses LangGraph for RAG (`rag_graph.py`). This refactor aligns the mindmap generation with existing patterns while preserving real-time streaming.

**Stakeholders**: Backend developers, frontend (no API changes).

## Goals / Non-Goals

**Goals**:
- Refactor mindmap generation to use `StateGraph` pattern
- Maintain real-time streaming via `OutputEvent` system
- Keep JSON node/edge output format for interactive canvas
- Preserve `explain_node()` and `expand_node()` for editing
- Follow existing LangGraph patterns from `rag_graph.py`

**Non-Goals**:
- Change output format to Mermaid (keep JSON for canvas)
- Modify frontend or API contracts
- Add new features (pure refactoring)

## Decisions

### Workflow Design
**Decision**: Use a graph with conditional branching for level expansion.

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Analyze    │ ──▶ │ Generate     │ ──▶ │ Expand Level   │ ◀─┐
│  Document   │     │ Root Node    │     │ (per parent)   │ ──┘
└─────────────┘     └──────────────┘     └────────────────┘
                                                │
                                                ▼
                                         ┌────────────┐
                                         │   Done     │
                                         └────────────┘
```

**Conditional Edge**: `expand_level` loops back to itself while `current_depth < max_depth` and there are nodes to expand.

**Alternatives considered**:
- Linear graph like POC: Too simple, loses level-by-level control
- Fully parallel branch generation: Complex, harder to debug

### State Schema
**Decision**: Use TypedDict with streaming callback.

```python
from typing import TypedDict, Callable, Awaitable

class MindmapState(TypedDict):
    # Input
    document_content: str
    document_title: str
    max_depth: int
    max_branches: int
    
    # Processing state
    current_depth: int
    nodes_to_expand: list[str]  # Node IDs pending expansion
    
    # Output accumulation
    nodes: dict[str, dict]  # node_id -> node_data
    edges: list[dict]       # edge data list
    root_id: str | None
    
    # Streaming callback (injected)
    emit_event: Callable[[OutputEvent], Awaitable[None]]
    
    # Error handling
    error: str | None
```

### Streaming from Graph Nodes
**Decision**: Pass an async callback via state for real-time event emission.

```python
async def generate_root(state: MindmapState) -> MindmapState:
    # ... generate node ...
    await state["emit_event"](OutputEvent(
        type=OutputEventType.NODE_ADDED,
        node_id=node.id,
        node_data=node.to_dict(),
    ))
    return {**state, "root_id": node.id, "nodes": {node.id: node.to_dict()}}
```

**Rationale**: LangGraph doesn't natively support streaming from nodes, but we can inject an async callback to bridge to the existing `OutputEvent` system.

### File Organization
**Decision**: Create new graph file, keep agent as facade.

```
application/graphs/
├── __init__.py
├── rag_graph.py        # Existing
└── mindmap_graph.py    # New: workflow definition

domain/agents/
└── mindmap_agent.py    # Refactored: uses graph internally
```

**Rationale**: Follows existing pattern where graphs are in `application/graphs/`.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Callback injection is non-standard LangGraph | Document pattern clearly; keep callback optional with default no-op |
| State dict size grows with many nodes | Use node IDs in state, keep full data in accumulator |
| Breaking existing streaming behavior | Add integration test comparing old vs new event sequence |

## Migration Plan

1. Create `mindmap_graph.py` with new workflow
2. Refactor `MindmapAgent.generate()` to invoke graph
3. Keep `explain_node()` and `expand_node()` unchanged initially
4. Verify streaming parity with manual testing
5. (Optional) Later refactor explain/expand to separate mini-graphs

## Open Questions
- Should `expand_node()` also become a graph, or stay procedural? (Defer - keep procedural for now)

