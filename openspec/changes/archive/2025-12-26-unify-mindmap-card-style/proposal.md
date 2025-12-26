# Change: Unify Mindmap Card Styles and Enable Full Editing

## Why
Currently there are two different mindmap card components with inconsistent visual styles and capabilities:
1. `MindMapCanvasNode` (used by `GenerationOutputsOverlay`) - has icon badge, drag handle, chips, but expanded view lacks editing capabilities
2. `MindMapCard` (used by `InspirationDock`) - different visual style, but opens `MindMapEditor` with full editing

This creates:
- Jarring visual inconsistency between generation states
- Missing editing capabilities when expanding from `MindMapCanvasNode`
- Users cannot freely zoom (pinch/scroll) or edit nodes in the canvas-positioned mindmap

## What Changes
- Unify visual styling: ensure consistent card appearance across all contexts
- Enable full editing in expanded view: use `MindMapEditor` instead of simple `FullMindMapRenderer`
- Editing capabilities include:
  - Free zoom (scroll wheel, pinch gestures, +/- buttons)
  - Canvas pan (drag background)
  - Layout switching (radial, tree, balanced)
  - Node editing (add, delete, edit label/content)
  - Export (PNG, JSON)

## Impact
- Affected specs: `studio`
- Affected code:
  - `app/frontend/src/components/studio/canvas-nodes/MindMapCanvasNode.tsx` - Replace `FullMindMapRenderer` with `MindMapEditor` in expanded modal
  - `app/frontend/src/components/studio/InspirationDock.tsx` - Use unified card component
  - `app/frontend/src/components/studio/mindmap/MindMapViews.tsx` - Potentially deprecate `MindMapCard`
