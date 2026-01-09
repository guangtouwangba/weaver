# Tasks

## 1. Core Algorithm Implementation

- [x] 1.1 Create `DirectGenerateState` TypedDict for workflow state
- [x] 1.2 Implement direct generation node with Chinese prompt
- [x] 1.3 Implement direct generation node with English prompt
- [x] 1.4 Add language detection/selection logic (zh/en/auto)
- [x] 1.5 Implement refinement node with deduplication prompts
- [x] 1.6 Add token counting utility (tiktoken) - Not needed, using full context
- [x] 1.7 Add MAX_DIRECT_TOKENS configuration (default 500K)

## 2. LangGraph Workflow

- [x] 2.1 Create 2-node workflow: generate → refine → parse
- [x] 2.2 Add conditional edge for error handling
- [x] 2.3 Wire workflow graph with START/END

## 3. Source Reference Support

- [x] 3.1 Implement PDF text annotator: add `[PAGE:X]` markers to document text
- [x] 3.2 Implement video transcript annotator: add `[TIME:MM:SS]` markers
- [x] 3.3 Update generation prompt to instruct LLM to preserve source markers
- [x] 3.4 Implement source marker parser: extract `[Page X]` and `[MM:SS]` from output
- [x] 3.5 Create SourceRef objects with type (pdf/video), page/timestamp
- [x] 3.6 Attach source_refs to MindmapNode

## 4. Output Parsing

- [x] 4.1 Implement Markdown to MindmapNode parser
- [x] 4.2 Handle heading (#) as root node
- [x] 4.3 Handle bullet points (-) with indentation for hierarchy
- [x] 4.4 Generate unique node IDs
- [x] 4.5 Create MindmapEdge for parent-child connections
- [x] 4.6 Assign depth and color properties
- [x] 4.7 Strip source markers from display label, store in source_refs

## 5. Streaming Integration

- [x] 5.1 Emit GENERATION_STARTED at workflow start
- [x] 5.2 Emit GENERATION_PROGRESS after each phase
- [x] 5.3 Emit NODE_ADDED for each parsed node (include source_refs)
- [x] 5.4 Emit EDGE_ADDED for each edge
- [x] 5.5 Emit GENERATION_COMPLETE with node count

## 6. Integration

- [x] 6.1 Update `MindmapAgent` to use new workflow
- [x] 6.2 Maintain backward compatibility with depth parameter
- [x] 6.3 Add language parameter to API
- [x] 6.4 Update document loading to add page/time markers before generation

## 7. Cleanup

- [x] 7.1 Remove old chunker module - N/A (not present in codebase)
- [x] 7.2 Remove old semantic_parser module - N/A (not present in codebase)
- [x] 7.3 Remove old tree_aggregation module - N/A (not present in codebase)
- [x] 7.4 Remove old clustering module - N/A (not present in codebase)
- [x] 7.5 Remove old embedding module - N/A (not present in codebase)
- [x] 7.6 Remove old mapreduce module - N/A (not present in codebase)

## 8. Validation

- [x] 8.1 Unit tests for Markdown parser (19 tests in test_mindmap_graph.py)
- [x] 8.2 Unit tests for source marker parser (13 tests in test_source_annotator.py)
- [ ] 8.3 Integration test: verify 2-phase workflow
- [ ] 8.4 Test with Chinese document
- [ ] 8.5 Test with English document
- [ ] 8.6 Test PDF page navigation
- [ ] 8.7 Test video timestamp navigation
- [ ] 8.8 Test refinement deduplication quality

Note: Integration tests (8.3-8.8) require running the full application with LLM services.
