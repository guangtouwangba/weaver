# Change: Optimize Canvas Performance for Large Node Sets

## Why
The current canvas implementation has severe performance issues during drag interactions, confirmed by profiling data:

**Measured Performance (Single Drag Operation):**
- **12.8 FPS** (8 frames in 626ms) - target is 60 FPS
- Context state updates: **5-12ms each** (should be <1ms)
- SummaryNode re-rendered **20 times** during drag
- Overlay re-rendered **20 times** during drag

**Console Log Evidence:**
```
[Perf][Context] State update took 11.60ms
[Perf][Context] State update took 9.00ms
[Perf][SummaryNode] Render count: 20
[Perf] Drag ended. Total frames: 8, Duration: 626ms, Avg FPS: 12.8
```

**Root Causes Identified:**
1. **Primary**: StudioContext triggers cascade re-renders on every drag position update
2. **Secondary**: $O(N)$ linear traversal for hit testing/selection (future scale concern)
3. **Secondary**: No viewport culling - all nodes rendered regardless of visibility

## What Changes

### Phase 1: Drag Performance (Critical - Current Issue)
- **Drag State Isolation**: Move drag position state out of React Context to prevent cascade re-renders
- **CSS Transform Optimization**: Use CSS transforms during drag instead of React state updates
- **RAF Throttling**: Throttle mouse move handlers to requestAnimationFrame cadence

### Phase 2: Scale Optimization (Future - Large Node Sets)
- **Spatial Indexing**: Integrate RBush library for $O(\log N)$ spatial queries
- **Viewport Culling**: Only render nodes within the visible viewport bounds
- **Grid Optimization**: Replace per-dot Circle components with single Konva Shape using native canvas API

## Impact
- Affected specs: `studio/spec.md` (extends Canvas Interaction and adds performance requirements)
- Affected code:
  - `app/frontend/src/components/studio/GenerationOutputsOverlay.tsx` (drag handling)
  - `app/frontend/src/components/studio/SummaryCanvasNode.tsx` (node rendering)
  - `app/frontend/src/contexts/StudioContext.tsx` (state management)
  - `app/frontend/src/components/studio/KonvaCanvas.tsx` (main canvas)
  - New file: `app/frontend/src/hooks/useSpatialIndex.ts`
  - New file: `app/frontend/src/hooks/useViewportCulling.ts`
- Dependencies: New npm package `rbush` (Phase 2)

## Non-Goals (MVP Constraints)
- Real-time collaboration (Yjs/CRDT) - future scope
- WebGL rendering upgrade - not needed until 50K+ nodes
- Level of detail (LOD) rendering - already specified for mindmap, extend if needed

