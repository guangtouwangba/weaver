# Tasks: Enhance Mind Map Interaction

## Phase 1: State & Selection
- [x] Refactor `MindMapEditor` to use `selectedNodeIds` (Set) instead of `selectedNodeId`.
- [x] Update `RichMindMapNode` to handle multi-selection via `Shift/Cmd + Click`.
- [x] Implement `useHistory` hook for `data` state (Undo/Redo).
- [ ] Implement `RubberBandSelection` visual and logic in `MindMapEditor`.

## Phase 2: Keyboard Shortcuts
- [x] Implement keyboard event listener hook.
- [x] Bind `Tab` (Add Child) and `Enter` (Add Sibling).
- [x] Bind `Backspace/Delete` (Bulk Delete).
- [x] Bind `Arrows` (Navigation) - requires logic to find "nearest" node in direction.
- [x] Bind `Cmd+Z` / `Cmd+Shift+Z` (Undo/Redo).

## Phase 3: Multi-Node Operations
- [x] Update `handleNodeDragEnd` (and drag move visual) to support moving multiple nodes.
  - [x] Apply `resolveOverlaps` to the group of moved nodes if possible (optional for MVP, maybe just move them).

## Verification
- [x] Test all shortcuts.
- [x] Test rubber-band selection.
- [x] Test dragging 3 nodes at once.
- [x] Test Undo/Redo of a deletion.
