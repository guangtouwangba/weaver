# Tasks: Canvas Node Editing & ID Fix

## Phase 1: Robust ID Generation
- [x] Refactor `addNodeToCanvas` in `StudioContext.tsx` to use `crypto.randomUUID()`. <!-- id: 1 -->
- [x] Scan codebase for other `Date.now()` based ID generation (e.g. edges) and fix. <!-- id: 2 -->

## Phase 2: Node Editing UI
- [x] Create `src/components/studio/canvas/NodeEditor.tsx` component. <!-- id: 3 -->
- [x] Add `editingNodeId` state to `KonvaCanvas.tsx`. <!-- id: 4 -->
- [x] Implement `handleNodeEdit` callback in `KonvaCanvas`. <!-- id: 5 -->
- [x] Update `handleNodeDoubleClick` to trigger edit for non-source nodes. <!-- id: 6 -->
- [x] Integrate `NodeEditor` overlay in `KonvaCanvas` render. <!-- id: 7 -->

## Phase 3: Polish
- [x] Update Context Menu to include "Edit" option. <!-- id: 8 -->
- [x] Connect `NodeEditor` onSave to `updateNode` action. <!-- id: 9 -->
- [x] Verify keyboard shortcuts (`Enter` to save, `Esc` to cancel). <!-- id: 10 -->

## Phase 4: Synthesis UI Refinements
- [x] Make `SynthesisResultCard` draggable on screen. <!-- id: 11 -->
- [x] Render visual connection lines (edges) from source nodes to pending calculation. <!-- id: 12 -->
- [x] Ensure "Add to Board" places node at the current pending card position. <!-- id: 13 -->

## Phase 5: Synthesis Real-time Integration
- [x] Integrate `useOutputWebSocket` in `KonvaCanvas`. <!-- id: 14 -->
- [x] Handle `node_added` event to update pending synthesis card. <!-- id: 15 -->
- [x] Ensure specific `task_id` is tracked for synthesis sessions. <!-- id: 16 -->

## Phase 6: Synthesis as Canvas Node (Redesign)
- [x] Make source nodes semi-transparent during synthesis (opacity 0.4). <!-- id: 17 -->
- [x] Render pending synthesis result as a Konva `Group` on the canvas. <!-- id: 18 -->
- [x] Style the Konva synthesis node to match the reference design (bright, with AI badge). <!-- id: 19 -->
- [x] Enable dragging of the Konva synthesis node. <!-- id: 20 -->
- [x] Add "Add to Board" / "Discard" buttons as Konva elements or HTML overlay anchor. <!-- id: 21 -->
- [x] Remove fixed HTML overlay `SynthesisResultCard` usage. <!-- id: 22 -->
