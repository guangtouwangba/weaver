# Add Canvas Node Deletion UI

## Goal Description
Enable users to delete AI-generated or manually-created canvas nodes that contain errors or are no longer needed. Currently, users can create and view nodes but cannot remove them, leading to canvas clutter when generation produces incorrect results.

## Impact Analysis
- **User Experience**: Provides essential cleanup capability for managing canvas workspace.
- **Scope**: Frontend-only change. Backend deletion API already exists (`DELETE /canvas/nodes/{node_id}`).
- **Components Affected**: 
  - `CanvasContextMenu.tsx` (add delete option)
  - `useCanvasActions.ts` (add deletion hook)
  - `KonvaCanvas.tsx` (keyboard shortcut support)
