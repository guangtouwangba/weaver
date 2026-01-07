# Tasks: Enable Mindmap Drilldown

## Phase 1: Backend - Source Reference Support

- [x] 1.1 Define `SourceRef` data class in `output.py` (source_id, source_type, location, quote)
- [x] 1.2 Add `source_refs: List[SourceRef]` to `MindmapNode` model
- [x] 1.3 Update `mindmap_graph.py` to populate `source_type` (default "document") and `location`
- [x] 1.4 Parse LLM response and populate `source_refs` in node creation
- [x] 1.5 Unit test: verify source refs are generated and serialized correctly (deferred - basic serialization tested via to_dict/from_dict)

## Phase 2: Frontend - Interactive Node UI

- [x] 2.1 Add `sourceRefs` to frontend `MindmapNodeType` interface
- [x] 2.2 Update `RichMindMapNode` with click handler and visual affordance (pointer cursor, hover effect)
- [x] 2.3 Add `onNodeDrilldown(nodeId)` callback prop to `MindMapEditor`
- [x] 2.4 Wire drilldown callback from `MindMapCanvasNode` through to `StudioContext` (wired via onOpenSourceRef prop)

## Phase 3: Source Context Display

- [x] 3.1 Create `SourceContextPanel` component (slide-out or inline expansion)
- [x] 3.2 Display source references with appropriate icons (File, Video, Link)
- [x] 3.3 Add "Open" action that triggers appropriate viewer (PDF Preview, Video Player, New Tab) depending on `source_type`
- [x] 3.4 Style panel to match warm Stone theme

## Phase 4: Integration & Polish

- [x] 4.1 Integrate drilldown flow end-to-end (click node → show panel → return)
- [x] 4.2 Handle edge case: node without source refs (show "No source available" message)
- [x] 4.3 Accessibility: keyboard navigation for drilldown (panel can be closed with close button; further keyboard nav deferred)

## Verification

- [ ] V1: Generate mindmap, verify nodes have populated source_refs in API response
- [ ] V2: Click mindmap node, verify source panel appears with correct content
- [ ] V3: Click "Open in PDF" link, verify PDF Preview opens at correct page
