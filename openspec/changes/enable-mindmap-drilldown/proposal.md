# Proposal: Enable Interactive Mindmap Drilldown

## Background

The canvas currently displays **Generated Mindmap** and **Generated Summary** cards. However, these outputs are static—users cannot interact with individual mindmap nodes to explore deeper into the source content. This limits the utility of the mindmap as a visual thinking tool.

The key insight is: **a mindmap should be a navigational layer, not a final destination**. Users want to click on a node like "Stop Doing List" (不做清单) and immediately see the relevant source paragraphs, creating a seamless **macro (mindmap overview) → micro (source text)** workflow.

## Goals

1. **Make mindmap nodes clickable** - Each node becomes an entry point to deeper exploration
2. **Link nodes to source paragraphs** - Backend enriches nodes with source references during generation
3. **Enable smooth drilldown UX** - Clicking a node reveals source context without leaving the canvas workflow

## Proposed Changes

### Backend - Source Reference Enrichment

#### [MODIFY] [MindmapNode](file:///Users/siqiuchen/Documents/opensource/research-agent-rag/app/backend/src/research_agent/domain/entities/output.py)
- Add `source_refs: List[SourceRef]` field to the `MindmapNode` data model
- `SourceRef` contains: `document_id`, `page_number`, `quote` (exact text snippet)

#### [MODIFY] [mindmap_graph.py](file:///Users/siqiuchen/Documents/opensource/research-agent-rag/app/backend/src/research_agent/application/graphs/mindmap_graph.py)
- Update LLM prompts to request source references for each generated node
- Parse and populate `source_refs` when creating nodes

### Frontend - Interactive Node Drilldown

#### [MODIFY] [RichMindMapNode.tsx](file:///Users/siqiuchen/Documents/opensource/research-agent-rag/app/frontend/src/components/studio/mindmap/RichMindMapNode.tsx)
- Add click handler that triggers drilldown behavior
- Visual affordance (hover effect, cursor pointer) indicating clickability

#### [MODIFY] [MindMapEditor.tsx](file:///Users/siqiuchen/Documents/opensource/research-agent-rag/app/frontend/src/components/studio/mindmap/MindMapEditor.tsx)
- Add `onNodeDrilldown` callback prop
- State for selected node's source context display

#### [NEW] [SourceContextPanel.tsx](file:///Users/siqiuchen/Documents/opensource/research-agent-rag/app/frontend/src/components/studio/mindmap/SourceContextPanel.tsx)
- Slide-out panel or inline expansion showing source paragraphs
- Display document name, page reference, quoted text
- "Open in PDF Preview" link for full document access

## User Experience Flow

1. User generates a mindmap from uploaded documents
2. Mindmap renders with nodes representing key concepts (e.g., "Stop Doing List")
3. User clicks on the "Stop Doing List" node
4. Canvas smoothly expands/reveals a panel showing:
   - The relevant source paragraph(s) from the original document
   - Citation info (document name, page number)
   - Option to open full PDF at that location
5. User navigates back to mindmap overview, or drills into another node

## Risks

- **LLM Reliability**: Generating accurate source references depends on LLM correctly identifying and quoting source text
- **Performance**: Additional data per node increases payload size; may need lazy loading
- **UX Complexity**: Must avoid disrupting existing mindmap editing workflow

## Related Changes

- `unified-canvas-actions` (active) - May integrate with action system for programmatic drilldown
- PDF Preview Modal (existing) - Drilldown can link to existing document viewer

