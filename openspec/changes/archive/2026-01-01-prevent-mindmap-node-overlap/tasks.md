# Tasks: Prevent Mind Map Node Overlap

## Implementation
- [x] Research overlap resolution strategies (e.g., Force-directed, Push-aside).
- [x] Implement `resolveOverlaps` algorithm in `layoutAlgorithms.ts`.
- [x] Integrate `resolveOverlaps` into `MindMapEditor.tsx` in `onDragEnd` handler.
- [x] Support recursive movement for subtrees (when a node is pushed, its children must move too).

## Verification
- [x] Verify nodes do not overlap when dragged manually.
- [x] Verify subtrees maintain their relative positions when the parent is pushed.
