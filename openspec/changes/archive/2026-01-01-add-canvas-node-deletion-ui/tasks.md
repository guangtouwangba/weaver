# tasks.md

## 1. Backend Integration
- [x] Add `handleDeleteNode` function to `useCanvasActions.ts` that calls `DELETE /canvas/nodes/{node_id}`
- [x] Add `deleteNode` API method to `lib/api.ts`

## 2. Context Menu (For Canvas Nodes)
- [x] Right-click context menu already has "删除节点" (Delete Node) option
- [x] Wire delete action to `handleDeleteNode` hook with API call

## 3. Keyboard Shortcuts
- [x] Add keyboard event listener in `KonvaCanvas.tsx` for `Delete`/`Backspace` keys
- [x] Ensure only selected nodes are deleted (uses API with optimistic updates)

## 4. Visual Feedback
- [ ] Show toast notification on successful deletion
- [ ] Show error toast if deletion fails

## 5. Testing
- [ ] Manual test: Right-click node -> Delete
- [ ] Manual test: Select node -> Press Delete key
- [ ] Manual test: Verify WebSocket sync if collaborative mode is active
