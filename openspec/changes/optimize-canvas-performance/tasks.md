## Phase 1: Drag Performance (Critical - Current Issue)

### 1. Isolate Drag State from Context

- [ ] 1.1 Refactor `GenerationOutputsOverlay.tsx`: Use `useRef` for drag position during active drag
- [ ] 1.2 Update DOM directly via CSS transform during drag (bypass React state)
- [ ] 1.3 Commit final position to state only on drag end (`mouseup`)
- [ ] 1.4 Verify drag achieves 60fps (manual test with console perf logs)

### 2. RAF Throttling

- [ ] 2.1 Add requestAnimationFrame throttling to mouse move handler
- [ ] 2.2 Ensure proper cleanup of RAF on unmount
- [ ] 2.3 Verify reduced state updates during drag (check console logs)

### 3. Memoize Canvas Components

- [ ] 3.1 Wrap `SummaryCanvasNode` with `React.memo` and custom equality function
- [ ] 3.2 Verify render count stays at 1-2 during drag of other nodes
- [ ] 3.3 Memoize other frequently re-rendered canvas children if needed

### 4. Phase 1 Validation

- [ ] 4.1 Verify drag FPS ≥ 55fps (was 12.8fps)
- [ ] 4.2 Verify context state updates < 1ms each (was 5-12ms)
- [ ] 4.3 Verify no functional regressions (drag still works, position persists)

---

## Phase 2: Scale Optimization (Future - Large Node Sets)

### 5. Setup and Dependencies

- [ ] 5.1 Install rbush package: `npm install rbush @types/rbush`
- [ ] 5.2 Create `app/frontend/src/hooks/useSpatialIndex.ts` with RBush integration

### 6. Spatial Indexing Integration

- [ ] 6.1 Implement `useSpatialIndex(nodes)` hook returning memoized RBush tree
- [ ] 6.2 Replace box selection O(N) loop with spatial index query in `KonvaCanvas.tsx`
- [ ] 6.3 Verify box selection works correctly with spatial index (manual test)

### 7. Viewport Culling

- [ ] 7.1 Create `app/frontend/src/hooks/useViewportCulling.ts` hook
- [ ] 7.2 Compute viewport bounds in canvas coordinates with 200px padding buffer
- [ ] 7.3 Filter rendered nodes using viewport culling hook
- [ ] 7.4 Verify nodes appear/disappear correctly during pan/zoom (manual test)

### 8. Grid Background Optimization

- [ ] 8.1 Create `app/frontend/src/components/studio/canvas/GridBackground.tsx` component
- [ ] 8.2 Replace Circle-based grid with single Konva Shape using native canvas API
- [ ] 8.3 Verify grid renders correctly at all zoom levels (manual test)

### 9. Phase 2 Validation

- [ ] 9.1 Test with 500+ nodes: verify smooth pan/zoom at 60fps
- [ ] 9.2 Test box selection performance with large node count
- [ ] 9.3 Verify no visual regressions in existing canvas features

