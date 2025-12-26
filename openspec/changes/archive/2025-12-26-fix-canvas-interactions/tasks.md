## 1. Fix Output Card Dragging

- [x] 1.1 Add `updateGenerationTaskPosition` function to `StudioContext` for updating task positions during drag
- [x] 1.2 Pass drag handlers (`onDragStart`, `onDragMove`, `onDragEnd`) from `GenerationOutputsOverlay` to output card components
- [x] 1.3 Implement drag position tracking in output cards using mouse events and update position state on drag end
- [x] 1.4 Ensure drag works with viewport transforms (scale and pan offset)

## 2. Fix Pan Mode (Hand Tool)

- [x] 2.1 Verify `toolMode` state is correctly passed from `CanvasPanelKonva` to `KonvaCanvas` and inspect for state sync issues
- [x] 2.2 Add `onContextMenu` handler to the canvas container Box to prevent default browser context menu and ensure events pass to Stage
- [x] 2.3 Ensure HTML overlay elements (`GenerationOutputsOverlay`) do not capture mouse events that should reach the Stage for panning
- [x] 2.4 Verify stage `handleStageMouseDown` correctly sets `isPanning` state in hand mode

## 3. Add Generation Loading Feedback for Context Menu

- [x] 3.1 Show loading card placeholder at click position immediately when generation starts via context menu
- [x] 3.2 Display "Generating..." state with spinner in the placeholder card (consistent with Inspiration Dock)
- [x] 3.3 Replace placeholder with actual output card when generation completes
- [x] 3.4 Ensure consistent visual feedback between Inspiration Dock and context menu generation flows

