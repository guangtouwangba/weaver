# Change: Hide Inspiration Dock When Outputs Exist + Fix Right-Click Generation

## Why
1. The Inspiration Dock is currently shown when the canvas is empty, serving as an entry point for generating content. However, once users have generated outputs (mindmaps, summaries, etc.), the dock becomes redundant visual clutter.
2. The right-click context menu currently uses a legacy generation method that doesn't place outputs on the canvas - it only shows them in the InspirationDock overlays, which is broken when the dock is hidden.

## What Changes
- Modify the visibility condition for `InspirationDock`: hide it when there are already completed outputs on the canvas
- Update `CanvasContextMenu` to use the concurrent generation method (`handleGenerateContentConcurrent`) which places outputs at the right-click position on the canvas
- Users retain full generation capability via right-click context menu when dock is hidden

## Impact
- Affected specs: `studio`
- Affected code:
  - `app/frontend/src/components/studio/KonvaCanvas.tsx` - Update dock visibility condition
  - `app/frontend/src/components/studio/CanvasContextMenu.tsx` - Use concurrent generation with position
  - `app/frontend/src/hooks/useCanvasActions.ts` - Ensure concurrent generation is exported and usable from context menu
