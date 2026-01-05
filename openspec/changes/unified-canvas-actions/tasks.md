# Tasks: Unified Canvas Actions API

## 1. Core Action System (P0)
- [ ] 1.1 **Types**: Define `CanvasAction` discriminated union type. @frontend
- [ ] 1.2 **Dispatcher**: Implement `useCanvasDispatch` hook to handle action execution. @frontend
- [ ] 1.3 **Node Actions**: Implement `addNode`, `updateNode`, `deleteNode`, `moveNode` actions. @frontend
- [ ] 1.4 **Edge Actions**: Implement `addEdge`, `updateEdge`, `deleteEdge`, `reconnectEdge` actions. @frontend
- [ ] 1.5 **Selection Actions**: Implement `selectNodes`, `clearSelection`, `selectAll` actions. @frontend
- [ ] 1.6 **Viewport Actions**: Implement `panTo`, `zoomTo`, `fitToContent` actions. @frontend

## 2. Integration Layer (P0)
- [ ] 2.1 **Context**: Create `CanvasActionsContext` to provide dispatch function globally. @frontend
- [ ] 2.2 **Callbacks**: Maintain backward-compatible `onNodesChange`/`onEdgesChange` callbacks. @frontend
- [ ] 2.3 **history**: Optional undo/redo stack for action history. @frontend

## 3. AI Agent Integration (P1)
- [ ] 3.1 **Schema**: Define JSON Schema for LLM function calling. @frontend
- [ ] 3.2 **Parser**: Implement natural language command parser. @frontend
- [ ] 3.3 **Chat Hook**: Create `useCanvasAgent` hook for chat-based control. @frontend
- [ ] 3.4 **UI**: Add canvas action suggestions in chat interface. @frontend
