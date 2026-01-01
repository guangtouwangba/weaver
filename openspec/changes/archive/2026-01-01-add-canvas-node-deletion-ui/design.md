# Design: Canvas Node Deletion

## Current State
- **Backend**: Deletion API exists at `DELETE /projects/{project_id}/canvas/nodes/{node_id}`
- **Frontend**: No user-facing deletion controls

## UX Approach
1. **Context Menu**: Right-click on a node shows "Delete" option
2. **Keyboard Shortcut**: `Delete` or `Backspace` key removes selected node
3. **Confirmation**: Optional for now (can add later if needed)

## Technical Approach

### 1. Hook Function (`useCanvasActions`)
Add `handleDeleteNode(nodeId: string)` that:
- Calls the existing backend API
- Updates local state optimistically
- Handles errors gracefully

### 2. Context Menu Integration
Update `CanvasContextMenu.tsx` to include:
```tsx
<MenuItem onClick={() => onDelete(node.id)}>
  <DeleteIcon /> Delete
</MenuItem>
```

### 3. Keyboard Support
In `KonvaCanvas.tsx`, add keyboard listener:
- Listen for `Delete` or `Backspace` when a node is selected
- Call `handleDeleteNode` with selected node ID

## Error Handling
- If deletion fails (404/409), show error toast
- If network fails, rollback optimistic update
