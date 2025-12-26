# Change: Fix Canvas Interaction Bugs

## Why
Three canvas interaction issues affect user experience: output cards cannot be dragged to reposition, pan mode (hand tool) does not allow canvas panning, and right-click context menu generation lacks loading feedback (unlike Inspiration Dock), leaving users uncertain if generation is in progress.

## What Changes
- Fix output card dragging: Connect drag handlers in `GenerationOutputsOverlay` and implement position state updates in `StudioContext`
- Fix pan mode: Ensure stage mouse events are not blocked by HTML overlays and that pan mode state is properly handled
- Add generation loading feedback for context menu: Show consistent loading indicator when generating content via right-click menu (same as Inspiration Dock)

## Impact
- Affected specs: `studio/spec.md`
- Affected code:
  - `app/frontend/src/components/studio/GenerationOutputsOverlay.tsx`
  - `app/frontend/src/components/studio/KonvaCanvas.tsx`
  - `app/frontend/src/components/studio/CanvasContextMenu.tsx`
  - `app/frontend/src/contexts/StudioContext.tsx`
  - `app/frontend/src/components/studio/canvas-nodes/SummaryCanvasNode.tsx`
  - `app/frontend/src/components/studio/canvas-nodes/MindMapCanvasNode.tsx`
  - `app/frontend/src/hooks/useCanvasActions.ts`

