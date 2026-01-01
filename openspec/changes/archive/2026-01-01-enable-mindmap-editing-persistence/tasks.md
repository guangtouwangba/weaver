# Tasks: Enable Mind Map Editing Persistence

## Backend
- [x] Define `UpdateOutputRequest` DTO in `research_agent/application/dto/output.py`.
- [x] Implement `update_output` in `OutputGenerationService`.
- [x] Add `PATCH /outputs/{output_id}` endpoint in `research_agent/api/v1/outputs.py`.

## Frontend
- [x] Update `outputsApi` in `lib/api.ts` to include `update` method.
- [x] Add `saveGenerationOutput` to `StudioContext`.
- [x] Wire `onDataChange` from `MindMapCanvasNode` through `GenerationOutputsOverlay` to `StudioContext`.
- [x] Verify changes persist after reload.
