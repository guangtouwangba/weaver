## 1. Frontend - Hide Dock When Outputs Exist

- [x] 1.1 Update `KonvaCanvas.tsx`: Add condition to check `generationTasks` for completed outputs
- [x] 1.2 Pass `generationTasks` or a derived `hasCompletedOutputs` boolean to the dock visibility logic

## 2. Frontend - Fix Right-Click Context Menu Generation

- [x] 2.1 Update `CanvasContextMenu.tsx` to receive `canvasViewport` for coordinate conversion
- [x] 2.2 Create helper function to convert screen coordinates (x, y from right-click) to canvas coordinates
- [x] 2.3 Update `CanvasContextMenu.tsx` to use `handleGenerateContentConcurrent` instead of `handleGenerateContent`
- [x] 2.4 Pass the converted canvas position to `handleGenerateContentConcurrent` for output placement

## 3. Verification

- [x] 3.1 Test: Right-click → Generate Mind Map → Output appears at click position
- [x] 3.2 Test: Right-click → Generate Summary → Output appears at click position  
- [x] 3.3 Test: After generating an output, InspirationDock is hidden
- [x] 3.4 Test: On empty canvas with documents, InspirationDock is visible
