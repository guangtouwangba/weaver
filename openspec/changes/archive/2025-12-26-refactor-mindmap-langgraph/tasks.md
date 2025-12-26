## 1. Create LangGraph Workflow

- [x] 1.1 Create `application/graphs/mindmap_graph.py`
  - Define `MindmapState` TypedDict with document_content, nodes, edges, emit_event callback
  - Add `analyze_document` node: extract key themes, prepare for root generation
  - Add `generate_root` node: create root MindmapNode, emit NODE_ADDED event
  - Add `expand_level` node: generate children for current level nodes, emit events

- [x] 1.2 Wire the graph edges
  - START → analyze_document → generate_root → expand_level
  - Add conditional edge: expand_level → expand_level (if depth < max_depth)
  - Add conditional edge: expand_level → END (if depth >= max_depth or no nodes)

- [x] 1.3 Implement event emission callback pattern
  - Create async callback type for OutputEvent emission
  - Inject callback via state for real-time streaming
  - Add default no-op callback for testing without streaming

## 2. Refactor MindmapAgent

- [x] 2.1 Update `MindmapAgent.generate()` to use the graph
  - Create emit_event callback that yields OutputEvents
  - Initialize MindmapState with document content and callback
  - Invoke compiled graph with state
  - Convert async generator pattern to graph invocation

- [x] 2.2 Preserve backward compatibility
  - Keep `BaseOutputAgent` inheritance
  - Maintain same OutputEvent sequence as before
  - Keep `explain_node()` and `expand_node()` unchanged

## 3. Testing

- [x] 3.1 Manual verification
  - Generate mindmap, verify real-time node appearance
  - Check level-by-level progression
  - Verify final node/edge count matches expectations

- [x] 3.2 Compare event sequences
  - Document expected event order: STARTED → NODE_ADDED (root) → NODE_ADDED (level 1) → LEVEL_COMPLETE → ... → COMPLETE
  - Verify new implementation matches existing behavior

## 4. Performance Optimization

- [x] 4.1 Add node count limits to prevent frontend freezing
  - Added `MAX_TOTAL_NODES = 50` hard cap in `mindmap_graph.py`
  - Early termination in `expand_level()` when limit is reached
  - Capacity check per branch to prevent overshooting

- [x] 4.2 Reduce default configuration
  - Changed defaults from `max_depth=3, max_branches=5` (156 nodes max)
  - To `max_depth=2, max_branches=4` (21 nodes max)
  - Updated in both `output_generation_service.py` and `generate_output.py`

