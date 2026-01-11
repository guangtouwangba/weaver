# Add Knowledge Export Module

## Goal
Implement the "Knowledge Liquidity Module" to allow users to export content from the Research Agent Studio seamlessly.
The initial focus (MVP) is on the **Smart Semantic Clipboard**, enabling users to copy canvas nodes as structured Markdown with `Ctrl+C`.

## Context
Based on the [Refined PRD](file:///openspec/changes/add-knowledge-export-module/REFINED_PRD.md), the goal is to eliminate "Vendor Lock-in Fear" and position the tool as a "Super Middleware".
Phase 1 (MVP) targets the "Smart Semantic Clipboard" functionality.

## Proposed Changes

### Frontend
- **Logic**: Implement `Spatial-to-Linear Mapping Protocol` in `src/lib/clipboard.ts`.
    - **Sorting**: Visual reading order (Z-Pattern) for mixed nodes.
    - **Formatting**: Convert various node types (Text, PDF, Video, Mindmap) to Markdown.
- **Interaction**: Update `KonvaCanvas.tsx` to handle `Ctrl+C` (Copy) shortcut.
    - Capture selected nodes.
    - Trigger conversion.
    - Write to system clipboard.
- **Feedback**: Show transient visual feedback (e.g., toast or badges) when copying.

### Scope (Phase 1 MVP)
- **Supported Formats**: Markdown (`text/plain`).
- **Supported Nodes**:
    - Note/Text Nodes
    - Source Nodes (PDF, Web, Video) -> Links/Citations
    - Mindmap Nodes -> Indented Lists/Headers
- **Images**: Markdown image links (source URL or Base64 if needed/feasible in MVP).

## Verification Plan
1.  **Manual Test**: Select multiple nodes (notes, videos) scattered on canvas -> `Ctrl+C` -> Paste in Notion/VSCode -> Verify order and format.
2.  **Manual Test**: Select a Mindmap branch -> `Ctrl+C` -> Paste -> Verify indentation/hierarchy.
3.  **Unit Test**: Test sorting logic in `clipboard.ts` with mock node positions.
