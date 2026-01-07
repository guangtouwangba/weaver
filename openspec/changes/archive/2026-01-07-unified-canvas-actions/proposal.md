# Proposal: Unified Canvas Actions API

## Background

The current canvas implementation has user-facing actions scattered across multiple components and hooks:
- `KonvaCanvas.tsx` uses callbacks like `onNodesChange`, `onEdgesChange`, `onNodeAdd` and handles selection/drag state internally
- `CanvasPanelKonva.tsx` provides viewport actions (`handleZoomIn`, `handleZoomOut`, `handleFitView`)
- `useCanvasActions.ts` provides functions like `handleAddNode`, `handleDeleteNode`, `handleSynthesizeNodes`, `handleGenerateContentConcurrent`
- `CanvasContextMenu.tsx` triggers actions at right-click positions
- No centralized, programmatic interface exists for external control (e.g., AI agents)

## Goals

1. **Create a unified Action dispatcher** - A centralized API that can execute canvas operations.
2. **Enable AI Agent integration** - Provide a chat-based interface for users to control the whiteboard via natural language commands.
3. **Support action composition** - Allow chaining multiple actions for complex operations.
4. **Maintain undo/redo capabilities** - Design actions to be reversible.

## Scope

### Frontend (`app/frontend/src`)

- **P0: Action System Core**
  - Define `CanvasAction` type with discriminated union for all action types
  - Implement `useCanvasDispatch` hook to execute actions
  - Refactor existing operations to use the action system

- **P1: AI Agent Integration**
  - Create `useCanvasAgent` hook for interpreting natural language commands
  - Define action schema for LLM function calling
  - Integrate with existing chat interface

## Risks

- **Complexity**: Adding an abstraction layer may introduce bugs if not carefully implemented
- **Performance**: Dispatching through a central point could add overhead
- **Backwards Compatibility**: Existing direct callbacks must continue working during migration

## Related Changes

- `improve-canvas-connections` (P0/P1 complete)
- `implement-project-chat` (archived)
