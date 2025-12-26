# Change: Fix Mindmap Node Overlap and Exponential Growth

## Why
Current mindmap generation has two critical issues:
1. **Exponential Node Growth**: With `max_depth=3` and `max_branches=5`, the mindmap generates 156 nodes (1 + 5 + 25 + 125), causing performance issues and overwhelming the user.
2. **Node Overlap**: Each parent calculates child positions independently without considering siblings' subtrees, causing visual overlap at deeper levels.

## What Changes
- **Backend**: Remove hardcoded position calculation from graph; emit nodes with `x=0, y=0` placeholder
- **Backend**: Reduce default `max_branches` from 5 to 4, and `max_depth` from 3 to 2 for reasonable node counts (1 + 4 + 16 = 21 nodes)
- **Frontend**: Apply layout algorithm (`layoutAlgorithms.ts`) when mindmap data is received, before rendering
- **Frontend**: Re-apply layout when new nodes stream in (debounced)

## Impact
- **Specs**: `agents` capability will be modified for position handling
- **Code**:
  - `application/graphs/mindmap_graph.py` - Remove position calculation, adjust defaults
  - `components/studio/mindmap/MindMapViews.tsx` - Apply layout on data load
  - `hooks/useCanvasActions.ts` - Apply layout after streaming complete

