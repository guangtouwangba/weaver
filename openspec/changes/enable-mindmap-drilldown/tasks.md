# Tasks: Enable Mindmap Drilldown

## Phase 1: Backend - Source Reference Support

- [ ] 1.1 Define `SourceRef` data class in `output.py` (document_id, page_number, quote)
- [ ] 1.2 Add `source_refs: List[SourceRef]` to `MindmapNode` model
- [ ] 1.3 Update `mindmap_graph.py` prompts to request source quotes for each node
- [ ] 1.4 Parse LLM response and populate `source_refs` in node creation
- [ ] 1.5 Unit test: verify source refs are generated and serialized correctly

## Phase 2: Frontend - Interactive Node UI

- [ ] 2.1 Add `sourceRefs` to frontend `MindmapNodeType` interface
- [ ] 2.2 Update `RichMindMapNode` with click handler and visual affordance (pointer cursor, hover effect)
- [ ] 2.3 Add `onNodeDrilldown(nodeId)` callback prop to `MindMapEditor`
- [ ] 2.4 Wire drilldown callback from `MindMapCanvasNode` through to `StudioContext`

## Phase 3: Source Context Display

- [ ] 3.1 Create `SourceContextPanel` component (slide-out or inline expansion)
- [ ] 3.2 Display source references: document name, page, quoted text
- [ ] 3.3 Add "Open in PDF" action that navigates to PDF Preview Modal at specific page
- [ ] 3.4 Style panel to match warm Stone theme

## Phase 4: Integration & Polish

- [ ] 4.1 Integrate drilldown flow end-to-end (click node → show panel → return)
- [ ] 4.2 Handle edge case: node without source refs (show "No source available" message)
- [ ] 4.3 Accessibility: keyboard navigation for drilldown

## Verification

- [ ] V1: Generate mindmap, verify nodes have popuplated source_refs in API response
- [ ] V2: Click mindmap node, verify source panel appears with correct content
- [ ] V3: Click "Open in PDF" link, verify PDF Preview opens at correct page
