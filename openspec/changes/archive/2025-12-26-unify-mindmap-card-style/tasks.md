## 1. Implementation

- [x] 1.1 Update `MindMapCanvasNode` expanded modal to use `MindMapEditor` instead of `FullMindMapRenderer`
- [x] 1.2 Remove redundant `FullMindMapRenderer` component from `MindMapCanvasNode.tsx`
- [x] 1.3 Update `InspirationDock` to use `MindMapCanvasNode` instead of `MindMapCard` for consistent styling
- [x] 1.4 Add overlay mode prop to `MindMapCanvasNode` (centered position without viewport transform)
- [x] 1.5 Deprecate or remove `MindMapCard` from `MindMapViews.tsx` (keep `MindMapFullView` as wrapper)
- [x] 1.6 Verify all editing features work in expanded view:
  - [x] Free zoom (scroll wheel, pinch gesture)
  - [x] Canvas pan (drag background)
  - [x] Layout switching
  - [x] Node add/delete/edit
  - [x] Export PNG/JSON
