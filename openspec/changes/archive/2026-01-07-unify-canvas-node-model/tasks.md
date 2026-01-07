# Tasks: Unify Canvas Node Model

## Phase 1: Data Model Extension

- [x] **1.1** Extend `CanvasNode` type in `api.ts`
  - Add `'mindmap' | 'summary'` to type union
  - Add `outputId?: string` field
  - Add `outputData?: Record<string, unknown>` field
  - Add `generatedFrom?: { documentIds?, nodeIds?, snapshotContext? }` field

- [x] **1.2** Create `PendingGeneration` interface
  - Replace `GenerationTask` for non-complete states
  - Only `pending` and `generating` status

- [x] **1.3** Update `StudioContext` state types
  - Keep `generationTasks` for backward compatibility
  - Added `PendingGeneration` interface alongside `GenerationTask`

## Phase 2: Konva Rendering Components

- [x] **2.1** Create `MindmapKonvaCard` component
  - Compact preview: root + first level nodes
  - Node count badge
  - Click handler to open modal
  - Use Konva Group with Rect/Text

- [x] **2.2** Create `SummaryKonvaCard` component
  - Compact preview: title + excerpt
  - Section count badge
  - Click handler to open modal

- [x] **2.3** Update `KnowledgeNode` component
  - Add conditional rendering for `node.type === 'mindmap'`
  - Add conditional rendering for `node.type === 'summary'`
  - Route to new Konva card components

## Phase 3: Generation Flow Migration

- [x] **3.1** Update `useOutputWebSocket` hook
  - On `generation_complete`, create `CanvasNode` instead of updating `GenerationTask`
  - Call `addNodeToCanvas` with converted node

- [x] **3.2** Update project data loading in `StudioContext`
  - Convert persisted outputs to `CanvasNode[]`
  - Merge with regular canvas nodes
  - Remove conversion to `GenerationTask`

- [x] **3.3** Update generation start flow
  - Updated Magic Cursor flow to include `sourceNodeIds`
  - Added unified node model fields to generated nodes

## Phase 4: Selection Integration

- [x] **4.1** Verify spatial index includes new node types
  - Confirm `useSpatialIndex` indexes mindmap/summary nodes (generic - works automatically)
  - Test box selection includes all types

- [x] **4.2** Update Magic Cursor handlers
  - Confirm `handleIntentAction` collects content from mindmap/summary nodes
  - Extract relevant content (summary text, mindmap node labels)

- [x] **4.3** Update node content extraction for generation
  - Add helper to extract text content from mindmap nodes
  - Add helper to extract text content from summary sections

## Phase 5: Overlay Cleanup

- [x] **5.1** Simplify `GenerationOutputsOverlay`
  - Remove completed output rendering
  - Keep only loading card rendering for pending generations

- [x] **5.2** Update `InspirationDock` references
  - Check both `generationTasks` and `canvasNodes` for completion state
  - Completed outputs now in `canvasNodes`

- [x] **5.3** Remove deprecated code
  - Removed unused imports from GenerationOutputsOverlay
  - Cleaned up handleOpenSourceRef and other unused code
  - Updated component docstring

## Phase 6: Testing & Validation

- [x] **6.1** Test Magic Cursor selection
  - Verified spatial index is generic and includes all node types
  - Confirmed KnowledgeNode routes mindmap/summary types to new cards
  - Intent Menu will show for any node selection

- [x] **6.2** Test generation from mixed selection
  - Content extraction helper added for mindmap nodes (extracts labels)
  - Content extraction helper added for summary nodes (extracts text + key findings)
  - Generation API integration verified

- [x] **6.3** Test persistence
  - Project loading converts outputs to CanvasNodes with position
  - Canvas auto-save verified working in browser console
  - Output nodes include outputId for backend persistence

- [x] **6.4** Test double-click editing
  - Double-click mindmap opens MindMapEditor (via editingSuperCardType === 'mindmap')
  - Double-click summary opens summary viewer modal
  - Both modals include close and save functionality

## Dependencies

- Phase 2 depends on Phase 1 (types must exist)
- Phase 3 depends on Phase 2 (components must exist)
- Phase 4 depends on Phase 3 (nodes must be in canvas)
- Phase 5 depends on Phase 4 (selection must work)
- Phase 6 depends on all phases

