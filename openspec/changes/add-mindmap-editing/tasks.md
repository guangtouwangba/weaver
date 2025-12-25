## 1. Layout Selection

- [x] 1.1 Create layout algorithm utilities: `radialLayout()`, `treeLayout()`, `balancedLayout()`
- [x] 1.2 Add layout selector UI (dropdown or button group) in MindMapFullView toolbar
- [x] 1.3 Implement layout application: recalculate node positions based on selected layout
- [x] 1.4 Store current layout type in state (default to balanced/radial)
- [x] 1.5 Animate layout transitions when switching between layouts

## 2. Interactive Canvas

- [x] 2.1 Enable `draggable` prop on MindMapNode Konva Group
- [x] 2.2 Add drag handlers to update node positions in local state
- [x] 2.3 Implement edge re-rendering when nodes are dragged (edges follow nodes)
- [x] 2.4 Add pan/zoom controls to the full view canvas (wheel zoom, drag to pan background)

## 3. Node Editing

- [x] 3.1 Add toolbar with Add/Delete/Edit actions in MindMapFullView
- [x] 3.2 Implement "Add Node" flow: click to add, specify parent, enter label
- [x] 3.3 Implement "Delete Node" flow: select node, click delete, cascade delete children
- [x] 3.4 Implement inline label editing on double-click
- [x] 3.5 Track edited state and show "unsaved changes" indicator

## 4. Export/Download

- [x] 4.1 Add Download button to toolbar with format options (PNG, JSON)
- [x] 4.2 Implement PNG export using Konva stage `toDataURL()` 
- [x] 4.3 Implement JSON export with current MindmapData structure
- [x] 4.4 Trigger browser download with appropriate filename

## 5. Performance Optimization

- [x] 5.1 Implement viewport culling: only render nodes within visible bounds + buffer zone
- [x] 5.2 Create LOD (Level of Detail) rendering: simplify nodes when zoomed out
  - [x] Hide content text at zoom < 0.7
  - [x] Show only labels at zoom < 0.5
  - [x] Render as simple shapes at zoom < 0.3
- [x] 5.3 Add throttling for drag updates (requestAnimationFrame or 60fps cap)
- [x] 5.4 Debounce edge recalculations during drag, full redraw on dragEnd
- [x] 5.5 Implement async layout calculation with Web Worker or `requestIdleCallback`
- [x] 5.6 Add loading indicator during heavy layout operations
- [x] 5.7 Batch node rendering during AI streaming (accumulate nodes, render every 100ms)
- [x] 5.8 Optimize React renders: use `React.memo`, stable keys, avoid unnecessary re-renders
- [x] 5.9 Implement proper cleanup: dispose Konva objects and listeners on unmount
- [x] 5.10 Add performance warning UI when node count > 200
- [x] 5.11 Implement "collapse branch" feature to reduce visible nodes
- [x] 5.12 Add "limit visible depth" option in settings
