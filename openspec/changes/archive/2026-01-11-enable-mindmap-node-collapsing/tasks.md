# Tasks: Enable Mindmap Node Collapsing

## Implementation
- [x] **State Model Extension**
  - Update `MindmapNode` interface in `frontend/src/lib/api.ts` to include optional `collapsed: boolean`.
- [x] **Node Toggle UI**
  - Modify `RichMindMapNode` to render a toggle button for nodes with children.
  - Add logic to calculate if a node has children (either by checking `edges` or a parent-child map).
- [x] **Visibility Filtering**
  - Implement ancestor-based visibility logic in `MindMapEditor`.
  - Filter `nodes` and `edges` before passing them to the Konva `Layer`.
- [x] **Persistence**
  - Ensure the `collapsed` boolean is preserved during state updates and saved to the backend.

## Verification
- [x] **Manual UI Test**
  - Generate a mindmap.
  - Collapse a branch and verify children disappear.
  - Expand the branch and verify children reappear.
  - Save the mindmap, refresh, and verify collapsed state is persisted.
