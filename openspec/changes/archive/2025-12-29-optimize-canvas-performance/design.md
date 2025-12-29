# Design: Canvas Performance Optimization

## Context

The infinite canvas is the core workspace for the Visual Thinking Assistant. Performance is critical for user experience. Profiling has revealed severe performance issues during basic drag operations.

**Profiling Results (Single Drag Operation):**
```
Duration: 626ms
Total frames: 8
Average FPS: 12.8 (target: 60)
Context state updates: 5-12ms each
SummaryNode renders: 20
Overlay renders: 20
```

**Identified Bottlenecks (Priority Order):**
1. **Critical**: StudioContext state updates cascade to all consumers on every drag position change
2. **Critical**: Each mouse move triggers full React reconciliation cycle
3. Future: Box selection uses $O(N)$ AABB intersection test
4. Future: No viewport culling - all nodes rendered regardless of visibility

**Target Performance:**
- 60fps during drag operations (currently 12.8 FPS)
- < 16ms frame time during any interaction
- Smooth pan/zoom with 5000+ nodes (future)

## Goals
- **Phase 1**: Fix drag performance to achieve 60fps (currently 12.8 FPS)
- **Phase 2**: Introduce spatial indexing for efficient spatial queries at scale
- **Phase 2**: Implement viewport culling to render only visible content
- Maintain existing functionality and API contracts
- Keep codebase maintainable (solo developer constraint)

## Non-Goals
- WebGL migration (not needed yet)
- Real-time collaboration infrastructure
- Mobile gesture optimization beyond current trackpad support

## Decisions

### Decision 0: Isolate Drag State from React Context (Phase 1 - Critical)

**What:** Move drag position tracking outside of React's state management during active drag operations.

**Why:**
- Current implementation updates `StudioContext` on every mouse move
- Each context update triggers re-render cascade to all context consumers
- Profiling shows 5-12ms per state update, causing 12.8 FPS during drag

**Implementation Strategy:**

Option A - **useRef for drag position (Recommended)**:
```typescript
// In GenerationOutputsOverlay.tsx
const dragPositionRef = useRef<{ x: number; y: number } | null>(null);

const handleMouseMove = (e: MouseEvent) => {
  if (!isDragging) return;
  
  // Update ref (no re-render)
  dragPositionRef.current = { x: e.clientX, y: e.clientY };
  
  // Update DOM directly via transform
  const element = document.getElementById(`node-${dragTaskId}`);
  if (element) {
    element.style.transform = `translate(${newX}px, ${newY}px)`;
  }
};

// Only commit to state on drag end
const handleMouseUp = () => {
  if (dragPositionRef.current) {
    // Single state update at end
    updateNodePosition(dragTaskId, dragPositionRef.current);
  }
  dragPositionRef.current = null;
};
```

Option B - **CSS custom properties** (alternative):
```typescript
// Update CSS variable instead of state
document.documentElement.style.setProperty('--drag-x', `${x}px`);
document.documentElement.style.setProperty('--drag-y', `${y}px`);
```

**Trade-offs:**
- Ref approach bypasses React's reconciliation (intentional for performance)
- Requires DOM manipulation during drag (acceptable for this use case)
- Final position committed to state on drag end maintains data consistency

### Decision 0.1: RAF Throttling for Mouse Move (Phase 1)

**What:** Use requestAnimationFrame to throttle mouse move handler to screen refresh rate.

**Why:**
- Mouse events fire faster than screen refresh (often 100+ events per 60fps frame)
- Processing every event wastes CPU and causes frame drops

**Implementation:**
```typescript
const rafIdRef = useRef<number | null>(null);

const handleMouseMove = (e: MouseEvent) => {
  if (rafIdRef.current) return; // Skip if RAF already scheduled
  
  rafIdRef.current = requestAnimationFrame(() => {
    // Process drag update here
    rafIdRef.current = null;
  });
};

useEffect(() => {
  return () => {
    if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
  };
}, []);
```

### Decision 0.2: Memoize Child Components (Phase 1)

**What:** Wrap SummaryCanvasNode and other canvas children with React.memo to prevent unnecessary re-renders.

**Why:**
- SummaryNode re-rendered 20 times during single drag (should be 0-1)
- Node content doesn't change during drag of another node

**Implementation:**
```typescript
const SummaryCanvasNode = React.memo(({ task, position, onDragStart, onToggleExpand }: Props) => {
  // Component implementation
}, (prevProps, nextProps) => {
  // Custom equality check - only re-render if this node's data changed
  return prevProps.task.id === nextProps.task.id &&
         prevProps.position.x === nextProps.position.x &&
         prevProps.position.y === nextProps.position.y &&
         prevProps.task.status === nextProps.task.status;
});
```

---

---

## Phase 2 Decisions (Future - Large Node Sets)

### Decision 1: Use RBush for Spatial Indexing

**What:** Integrate [RBush](https://github.com/mourner/rbush), a high-performance JavaScript R-tree library.

**Why:**
- Proven in production (used by Mapbox, Leaflet)
- Simple API: `load()`, `search()`, `insert()`, `remove()`
- Zero dependencies, ~6KB minified
- $O(\log N)$ queries instead of $O(N)$

**Alternatives Considered:**
- **Quadtree**: Better for point data, but canvas has variable-sized rectangles
- **Custom AABB tree**: More development time, harder to maintain
- **No spatial index (status quo)**: Unacceptable performance at scale

**Trade-offs:**
- Extra memory for index structure (~32 bytes per node)
- Index rebuild needed on node batch changes (acceptable with Konva's rendering model)

### Decision 2: React Hook Pattern for Index Management

**What:** Create `useSpatialIndex(nodes)` hook that returns a memoized RBush tree.

**Why:**
- Automatic index rebuild when nodes change
- Clean integration with React's rendering cycle
- Reusable across canvas components

**Implementation:**
```typescript
interface SpatialItem {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  nodeId: string;
}

function useSpatialIndex(nodes: CanvasNode[]): RBush<SpatialItem> {
  return useMemo(() => {
    const tree = new RBush<SpatialItem>();
    const items = nodes.map(node => ({
      minX: node.x,
      minY: node.y,
      maxX: node.x + (node.width || 280),
      maxY: node.y + (node.height || 200),
      nodeId: node.id,
    }));
    tree.load(items); // Bulk load is 2-3x faster than individual inserts
    return tree;
  }, [nodes]);
}
```

### Decision 3: Viewport Culling Strategy

**What:** Compute viewport bounds in canvas coordinates and query spatial index for visible nodes only.

**Why:**
- Render time scales with visible nodes, not total nodes
- Works naturally with RBush's bounding box queries

**Implementation:**
```typescript
function useViewportCulling(
  viewport: Viewport, 
  dimensions: { width: number; height: number },
  spatialIndex: RBush<SpatialItem>,
  nodes: CanvasNode[]
): CanvasNode[] {
  return useMemo(() => {
    const bounds = {
      minX: -viewport.x / viewport.scale,
      minY: -viewport.y / viewport.scale,
      maxX: (-viewport.x + dimensions.width) / viewport.scale,
      maxY: (-viewport.y + dimensions.height) / viewport.scale,
    };
    
    // Add padding to prevent pop-in during fast panning
    const padding = 200;
    const paddedBounds = {
      minX: bounds.minX - padding,
      minY: bounds.minY - padding,
      maxX: bounds.maxX + padding,
      maxY: bounds.maxY + padding,
    };
    
    const visibleItems = spatialIndex.search(paddedBounds);
    const visibleIds = new Set(visibleItems.map(item => item.nodeId));
    return nodes.filter(node => visibleIds.has(node.id));
  }, [viewport, dimensions, spatialIndex, nodes]);
}
```

### Decision 4: Grid Optimization with Konva Shape

**What:** Replace per-dot `<Circle>` components with a single `<Shape>` using native canvas API.

**Why:**
- Current approach creates O(N²) React elements for visible grid
- Single draw call is orders of magnitude faster
- Native canvas `arc()` is highly optimized

**Before (current):**
```tsx
// Creates thousands of Circle components
{dots.map(dot => <Circle key={dot.key} x={dot.x} y={dot.y} radius={1.5} fill="#E5E7EB" />)}
```

**After (optimized):**
```tsx
<Shape
  sceneFunc={(ctx) => {
    ctx.fillStyle = '#E5E7EB';
    for (let x = startX; x <= endX; x += gridSize) {
      for (let y = startY; y <= endY; y += gridSize) {
        ctx.beginPath();
        ctx.arc(x, y, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }}
  listening={false}
/>
```

### Decision 5: Code Modularization Strategy

**What:** Extract canvas logic into focused modules without breaking existing API.

**Structure:**
```
components/studio/
├── KonvaCanvas.tsx           # Main component (reduced from 2100 to ~800 lines)
├── canvas/
│   ├── GridBackground.tsx    # Optimized grid rendering
│   ├── KnowledgeNode.tsx     # Extracted node component
│   └── EdgeRenderer.tsx      # Edge rendering logic
hooks/
├── useSpatialIndex.ts        # RBush integration
├── useViewportCulling.ts     # Viewport-based filtering
└── useCanvasActions.ts       # (existing) action handlers
```

**Why:**
- Smaller files are easier to maintain for solo developer
- Clear separation of concerns
- Each module can be optimized independently

## Risks / Trade-offs

### Phase 1 Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| DOM manipulation bypasses React | State/UI desync | Commit to state on drag end; use data attributes for tracking |
| useRef pattern harder to debug | Dev experience | Add console logs in dev mode; remove in prod |
| Over-memoization | Stale renders | Custom equality check only compares relevant props |

### Phase 2 Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| RBush adds bundle size | +6KB | Acceptable for performance gains |
| Index rebuild on every node change | Could cause jank | Use `useMemo` + bulk load; consider debouncing for rapid changes |
| Viewport culling causes pop-in | Visual artifact during fast pan | Add padding buffer (200px) |
| Refactoring breaks existing features | Regression | Incremental changes with manual testing |

## Migration Plan

### Phase 1: Drag Performance (Priority - Current Blocker)
1. Isolate drag state from React Context using useRef
2. Add RAF throttling to mouse move handlers
3. Memoize SummaryCanvasNode and other canvas children
4. Validate: Achieve ≥55fps during drag (currently 12.8fps)

### Phase 2: Scale Optimization (Future)
5. Add RBush dependency and `useSpatialIndex` hook (non-breaking)
6. Replace box selection with spatial query
7. Implement viewport culling for node rendering
8. Optimize grid background
9. Validate: Smooth 60fps with 500+ nodes

Each step can be tested independently before proceeding.

## Open Questions

### Phase 1
1. **Should we use a drag library (e.g., @dnd-kit, react-dnd)?** Current custom implementation has issues; libraries may handle performance better but add bundle size.
2. **Keep perf logging in production?** Current `[Perf]` console logs are useful for debugging - decide if they should be conditional on dev mode.

### Phase 2
3. **Should we implement LOD for main canvas nodes?** Currently only specified for mindmap. May be useful if users create very dense layouts.
4. **Edge rendering optimization?** Edges between off-screen nodes could be simplified or hidden. Defer to follow-up if needed.
5. **Performance metrics/monitoring?** Consider adding dev-mode FPS counter for validation.

