# Tasks: Synthesize Canvas Nodes

## Phase 1: Backend (AI & API)
- [x] Create `SynthesisAgent` (inheriting `BaseAgent`).
  - [x] Implement `synthesize` method with prompt for consolidation (Insight, Recommendation, Risk).
  - [x] Define output schema/parsing.
- [x] Add `start_synthesize_nodes` to `OutputGenerationService`.
- [x] Add `POST /api/v1/outputs/{output_id}/synthesize` endpoint.
  - [x] Validation: verify output and node ownership.

## Phase 2: Frontend (Interaction & Visuals)
- [x] Add merge detection state (`mergeTargetNodeId`, `draggedNodeId`, `isSynthesizing`).
- [x] Add `synthesize` method to `outputsApi`.
- [x] Add `handleNodeDragMove` for proximity detection.
- [x] Add `isMergeTarget` purple glow highlight to `RichMindMapNode`.
- [x] Add `handleNodeDragEndWithMerge` to trigger merge flow.
- [x] Add `handleSynthesizeNodes` and `handleCancelMerge` callbacks.
- [x] Add "Merge with AI insights?" prompt overlay.
- [x] Add "Synthesizing..." loading overlay.
- [x] Implement `SynthesisModeMenu` component (Connect, Inspire, Debate).
- [x] Integrate mode selection into `handleNodeDragEndWithMerge`.

## Phase 3: Synthesis Modes (Refinement)
- [x] **Backend**: Update `SynthesisAgent` to support multiple prompt strategies.
- [x] **Backend**: Update API schema to accept `mode` enum.
- [x] **Frontend**: Design and implement the ephemeral mode selection menu.
- [x] **Frontend**: Pass selected mode to the synthesis API.
