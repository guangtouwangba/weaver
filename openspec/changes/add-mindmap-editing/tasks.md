## 1. Layout Selection

- [ ] 1.1 Create layout algorithm utilities: `radialLayout()`, `treeLayout()`, `balancedLayout()`
- [ ] 1.2 Add layout selector UI (dropdown or button group) in MindMapFullView toolbar
- [ ] 1.3 Implement layout application: recalculate node positions based on selected layout
- [ ] 1.4 Store current layout type in state (default to balanced/radial)
- [ ] 1.5 Animate layout transitions when switching between layouts

## 2. Interactive Canvas

- [ ] 2.1 Enable `draggable` prop on MindMapNode Konva Group
- [ ] 2.2 Add drag handlers to update node positions in local state
- [ ] 2.3 Implement edge re-rendering when nodes are dragged (edges follow nodes)
- [ ] 2.4 Add pan/zoom controls to the full view canvas (wheel zoom, drag to pan background)

## 3. Node Editing

- [ ] 3.1 Add toolbar with Add/Delete/Edit actions in MindMapFullView
- [ ] 3.2 Implement "Add Node" flow: click to add, specify parent, enter label
- [ ] 3.3 Implement "Delete Node" flow: select node, click delete, cascade delete children
- [ ] 3.4 Implement inline label editing on double-click
- [ ] 3.5 Track edited state and show "unsaved changes" indicator

## 4. Export/Download

- [ ] 4.1 Add Download button to toolbar with format options (PNG, JSON)
- [ ] 4.2 Implement PNG export using Konva stage `toDataURL()` 
- [ ] 4.3 Implement JSON export with current MindmapData structure
- [ ] 4.4 Trigger browser download with appropriate filename

## 5. Performance Optimization

- [ ] 5.1 Implement viewport culling: only render nodes within visible bounds + buffer zone
- [ ] 5.2 Create LOD (Level of Detail) rendering: simplify nodes when zoomed out
  - [ ] Hide content text at zoom < 0.7
  - [ ] Show only labels at zoom < 0.5
  - [ ] Render as simple shapes at zoom < 0.3
- [ ] 5.3 Add throttling for drag updates (requestAnimationFrame or 60fps cap)
- [ ] 5.4 Debounce edge recalculations during drag, full redraw on dragEnd
- [ ] 5.5 Implement async layout calculation with Web Worker or `requestIdleCallback`
- [ ] 5.6 Add loading indicator during heavy layout operations
- [ ] 5.7 Batch node rendering during AI streaming (accumulate nodes, render every 100ms)
- [ ] 5.8 Optimize React renders: use `React.memo`, stable keys, avoid unnecessary re-renders
- [ ] 5.9 Implement proper cleanup: dispose Konva objects and listeners on unmount
- [ ] 5.10 Add performance warning UI when node count > 200
- [ ] 5.11 Implement "collapse branch" feature to reduce visible nodes
- [ ] 5.12 Add "limit visible depth" option in settings

