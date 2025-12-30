# Proposal: Implement Project Chat

## Goal
Enable users to interact with the project content via a chat interface on the whiteboard. This includes asking questions relative to the project context, uploading documents, and seamlessly dragging content between the chat and the canvas/sources.

## Context
Currently, the whiteboard (`CanvasPanelKonva`) allows node manipulation and some source interaction. There is no dedicated chat interface for Q&A on the canvas. Users need a way to query their project documents and leverage the AI to summarize or extract information directly onto the board.

## Changes
### UI
- Add a floating/fixed "Chat" button at the bottom of the canvas.
- Implement a `ChatPanel` overlay/component that slides up or appears.
- Support Drag-and-Drop:
    - Drop `Source` or `CanvasNode` into Chat Input -> Adds to context.
    - Drop Chat Message/Response onto Canvas -> Creates a new `CanvasNode` (Note).

### Backend
- New API endpoint `POST /api/chat/project` (or similar) that accepts:
    - `query`: User question.
    - `context_items`: List of dropped items (source IDs, text content).
    - `project_id`: Current project.
- Backend using RAG to answer based on project documents + provided context.
- Return response with `citations` (source, page, quote).

## Implementation Strategy
1.  **Phase 1: UI Skeleton**: Button + Chat Panel.
2.  **Phase 2: RAG Backend**: Connect to existing RAG pipes or create new one for specific context.
3.  **Phase 3: DnD Integration**: Connect Konva Drag events to React Drop zones and vice versa.

