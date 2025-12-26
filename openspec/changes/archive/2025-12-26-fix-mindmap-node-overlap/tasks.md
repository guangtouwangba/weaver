## 1. Backend Changes

- [x] 1.1 Update `mindmap_graph.py` defaults
  - Changed `max_depth` default from 3 to 2
  - Changed `max_branches` default from 5 to 4
  - Updated `MindmapAgent.__init__` defaults accordingly

- [x] 1.2 Remove position calculation from backend
  - Set all generated nodes to `x=0, y=0`
  - Removed `_calculate_child_positions()` function
  - Kept `parentId` and `depth` fields for frontend layout

## 2. Frontend Layout Integration

- [x] 2.1 Apply layout in MindMapViews when data is set
  - Imported `applyLayout` from `layoutAlgorithms.ts`
  - Applied balanced layout in `MindMapRenderer` using `useMemo`
  - Canvas dimensions calculated from preview width/height/scale

- [x] 2.2 Apply layout after streaming completes
  - In `useCanvasActions.ts`, apply layout when GENERATION_COMPLETE received
  - Layout applied once at completion (not during streaming)

## 3. Testing

- [x] 3.1 Verify node count reduction
  - With default settings (depth=2, branches=4): 1 + 4 + 16 = 21 nodes max
  - Backend code verified to use correct defaults

- [x] 3.2 Verify no overlap
  - Layout now applied by frontend using `applyLayout` from `layoutAlgorithms.ts`
  - Balanced layout used by default for preview and editor

