# Tasks: Canvas Command API with NLU

## 0. Natural Language Understanding (P0)

- [ ] 0.1 **Context Builder**: Create `CanvasContext` builder that collects canvas state for LLM
  - Selected nodes with content preview
  - Viewport position and visible bounds
  - Recent nodes list
  - Available documents
  
- [ ] 0.2 **Tool Schema**: Define LLM function calling schema for canvas tools
  - `addNode`, `deleteNodes`, `updateNode`, `moveNode`
  - `connect`, `disconnect`
  - `generate`, `synthesize`
  - `search` (query, not action)
  
- [ ] 0.3 **System Prompt**: Write canvas agent system prompt
  - Pronoun resolution rules ("this", "these", "here")
  - Position intelligence (near selected, viewport center)
  - Examples for common commands
  
- [ ] 0.4 **NLU Service**: Create `CanvasNLUService` that:
  - Receives user input + canvas context
  - Calls LLM with tool definitions
  - Parses tool call response into `CanvasAction`
  - Validates parameters
  
- [ ] 0.5 **Integration**: Connect NLU to chat endpoint
  - Detect canvas command intent
  - Build context from frontend state
  - Execute action and return result

## 1. Edge API (P0)

- [ ] 1.1 **DTO**: Add `CreateEdgeRequest`, `UpdateEdgeRequest`, `EdgeOperationResponse` to `dto/canvas.py`
- [ ] 1.2 **Use Cases**: Create `create_edge.py`, `update_edge.py`, `delete_edge.py` in `use_cases/canvas/`
- [ ] 1.3 **Endpoints**: Add edge CRUD endpoints to `api/v1/canvas.py`
- [ ] 1.4 **Validation**: Edge source/target must exist, no duplicate edges

## 2. Batch Operations (P0)

- [ ] 2.1 **DTO**: Add `BatchDeleteNodesRequest` to `dto/canvas.py`
- [ ] 2.2 **Use Case**: Create `batch_delete_nodes.py` - delete nodes and their connected edges
- [ ] 2.3 **Endpoint**: Add `POST /projects/{id}/canvas/nodes/batch-delete`

## 3. Unified Action Endpoint (P1)

- [ ] 3.1 **DTO**: Define `CanvasActionRequest` discriminated union for all action types
- [ ] 3.2 **Use Case**: Create `execute_action.py` - route action to appropriate handler
- [ ] 3.3 **Endpoint**: Add `POST /projects/{id}/canvas/actions`
- [ ] 3.4 **History**: Store action in history for undo support

## 4. AI Generation API (P1)

- [ ] 4.1 **Generate**: Extend existing mindmap generation to support command trigger
- [ ] 4.2 **Synthesize**: Create `synthesize_nodes.py` use case for node synthesis
- [ ] 4.3 **Endpoints**: Add `/generate` and `/synthesize` endpoints

## 5. Real-time Sync (P2)

- [ ] 5.1 **WebSocket Events**: Broadcast `canvas_action` events when actions complete
- [ ] 5.2 **Client Sync**: Frontend receives and applies remote actions
- [ ] 5.3 **Conflict Resolution**: Last-write-wins with version check

## 6. Action History (P2)

- [ ] 6.1 **Schema**: Add `canvas_action_history` table
- [ ] 6.2 **Undo/Redo**: Implement action reversal logic
- [ ] 6.3 **API**: Add `/canvas/undo` and `/canvas/redo` endpoints

