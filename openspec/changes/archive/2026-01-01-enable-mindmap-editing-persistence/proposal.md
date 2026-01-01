# Proposal: Enable Mind Map Editing and Persistence

## Goal
Allow users to edit generated mind maps (add/remove/edit nodes) and persist these changes to the backend. Currently, users can edit mind maps in the UI (via `MindMapEditor`), but these changes are not saved to the persistent storage and are lost on refresh.

## Problem
- `MindMapCanvasNode` uses `MindMapEditor` which supports full editing capabilities.
- However, the `onSave` callback is not effectively wired to a backend persistence method.
- The `outputsApi` currently lacks an endpoint to update the `data` of an existing output.

## Solution

### 1. Backend API Updates
- Add a new endpoint `PATCH /api/v1/projects/{project_id}/outputs/{output_id}`.
- This endpoint will accept a partial update payload, specifically allowing updates to `data` (MindmapData) and `title`.

### 2. Frontend Integration
- **API Client**: Update `outputsApi` in `api.ts` to include the `update` method.
- **Context**: Add `saveGenerationResult(taskId: string, data: any)` to `StudioContext`.
  - This function will find the output ID associated with the task and call the new API endpoint.
  - It will also update the local state in `generationTasks`.
- **UI Wiring**:
  - Update `GenerationOutputsOverlay` to pass a handler to `MindMapCanvasNode`'s `onDataChange` prop.
  - This handler will call `saveGenerationResult` in `StudioContext`.

## Impact
- **Backend**: New endpoint in `outputs` controller.
- **Frontend**: Updates to `api.ts`, `StudioContext.tsx`, and `GenerationOutputsOverlay.tsx`.
