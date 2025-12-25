## 1. Implementation
- [x] 1.1 Verify Backend Streaming
    - Ensure `MindmapAgent` emits `NODE_ADDED` events correctly.
    - Verify `OutputGenerationService` propagates these events to the frontend via SSE/WebSocket (whichever is used).
- [x] 1.2 Frontend: State Management
    - Update `useOutputGeneration` (or equivalent) to handle `MindmapData` accumulation from stream events.
    - Store nodes and edges in a state that triggers efficient re-renders.
- [x] 1.3 Frontend: Mind Map Renderer (Konva)
    - Create `MindMapNode` Konva component (shape, label, color).
    - Create `MindMapEdge` Konva component (connecting lines).
    - Implement "growth" animation (e.g., opacity/scale transition when node is added).
    - Implement automatic layouting (simple tree layout algorithm).
- [x] 1.4 Frontend: Views
    - Implement `MindMapCard` (minimized, read-only or simple interaction).
    - Implement `MindMapFullView` (maximized, zoomable/pannable).
    - Add toggle interactions (minimize/maximize).
- [x] 1.5 Integration
    - Add "Generate Mind Map" button to Inspiration Dock (similar to Summary).
    - Display the result in the dock/workspace.

