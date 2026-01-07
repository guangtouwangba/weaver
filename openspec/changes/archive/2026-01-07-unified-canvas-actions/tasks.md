# Tasks: Unified Canvas Actions API

## 1. Core Action System (P0)
- [x] 1.1 **Types**: Define `CanvasAction` discriminated union type in `lib/canvasActions.ts`. @frontend
- [x] 1.2 **Dispatcher**: Implement `useCanvasDispatch` hook to handle action execution in `hooks/useCanvasDispatch.ts`. @frontend
- [x] 1.3 **Node Actions**: Implement `addNode`, `updateNode`, `deleteNode`, `deleteNodes`, `moveNode` actions. @frontend
- [x] 1.4 **Edge Actions**: Implement `addEdge`, `updateEdge`, `deleteEdge`, `reconnectEdge` actions. @frontend
- [x] 1.5 **Selection Actions**: Implement `selectNodes`, `selectEdge`, `clearSelection`, `selectAll` actions. @frontend
- [x] 1.6 **Viewport Actions**: Implement `panTo`, `zoomTo`, `zoomIn`, `zoomOut`, `fitToContent` actions. @frontend

## 2. Integration Layer (P0)
- [x] 2.1 **Context**: Create `CanvasActionsContext` in `contexts/CanvasActionsContext.tsx`. @frontend
- [x] 2.2 **Callbacks**: Backward-compatible callbacks maintained in existing components. @frontend
- [x] 2.3 **History**: Implement undo/redo history stack in `hooks/useActionHistory.ts`. @frontend

## 3. Slash Command System (P0)
- [x] 3.1 **Parser**: Implement slash command parser in `lib/commandParser.ts`. @frontend
- [x] 3.2 **Command Registry**: Create command definitions with syntax, aliases, and validation rules. @frontend
- [x] 3.3 **Autocomplete**: Implement command autocomplete in CommandPalette. @frontend
- [x] 3.4 **Command Palette**: Add `CommandPalette.tsx` component integrated with `ChatOverlay.tsx`. @frontend
- [x] 3.5 **Help System**: Implement `/help` command and inline documentation. @frontend

## 4. AI Agent Integration (P1)
- [x] 4.1 **Schema**: Define JSON Schema for LLM function calling in `lib/canvasAgentSchema.ts`. @frontend
- [x] 4.2 **Agent Hook**: Create `useCanvasAgent` hook in `hooks/useCanvasAgent.ts`. @frontend
- [x] 4.3 **Command Output**: System prompt and function-to-command conversion in `canvasAgentSchema.ts`. @frontend
- [x] 4.4 **Confirmation UI**: Add `ActionConfirmationPanel.tsx` for reviewing AI-suggested actions. @frontend
