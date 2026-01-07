# Proposal: Canvas Command API with Natural Language Understanding

## Why

The frontend has implemented a slash command system (CommandPalette), but the system lacks:

1. **Natural Language → Action Translation** - Users should say "add a note about X" instead of `/add-node "X"`
2. **Context-Aware Parameter Inference** - LLM should know selected nodes, visible area, document context
3. **Intent Disambiguation** - "Connect these" needs to understand what "these" refers to
4. **Smart Defaults** - Position, color, size should be intelligently chosen based on canvas state

Additionally, backend API is incomplete:
- No endpoints for edge CRUD, batch operations
- No AI generation command support
- No action history for undo/redo

## What Changes

### Natural Language Understanding Layer

- **Intent Detection** - Classify user input into canvas action categories
  - Node operations: "add a note", "delete this", "move it here"
  - Edge operations: "connect A and B", "link these together"
  - Generation: "create a mindmap", "summarize these documents"
  - Query: "what nodes mention X?" (not an action, but retrieval)

- **Parameter Extraction** - Extract structured parameters from natural language
  - Content: "add a note about **quantum computing**" → `{ content: "quantum computing" }`
  - Position: "put it **in the top left**" → `{ x: 100, y: 100 }`
  - References: "connect **this** to **that**" → resolve to actual node IDs
  - Attributes: "make it **yellow**" → `{ color: "yellow" }`

- **Context Injection** - Provide canvas state to LLM for smart inference
  - Selected nodes: IDs and content summaries
  - Visible viewport: coordinates and scale
  - Recent nodes: last 5 created/modified
  - Document context: available source documents

- **LLM Function Calling Schema** - Structured output for reliable parsing
  - Define JSON schema for each action type
  - Use tool/function calling API (OpenAI, Claude, etc.)
  - Validate output before execution

### Backend API Additions

- **Edge endpoints** - CRUD operations for canvas edges
  - `POST /projects/{id}/canvas/edges` - Create edge
  - `PUT /projects/{id}/canvas/edges/{edge_id}` - Update edge
  - `DELETE /projects/{id}/canvas/edges/{edge_id}` - Delete edge

- **Batch operations**
  - `POST /projects/{id}/canvas/nodes/batch-delete` - Delete multiple nodes
  - `POST /projects/{id}/canvas/actions` - Execute action (unified endpoint)

- **AI generation endpoints**
  - `POST /projects/{id}/canvas/generate` - Generate content (mindmap, summary, etc.)
  - `POST /projects/{id}/canvas/synthesize` - Synthesize nodes into insight

- **WebSocket enhancements**
  - Broadcast canvas action events for real-time sync
  - Support action history for undo/redo

### Data Model

- **Edge entity** - Add proper edge model with relation types
- **Action history** - Store action log for undo/redo

## Impact

- **Affected specs**: `canvas-api` (new), `studio`
- **Affected code**:
  - `app/backend/src/research_agent/api/v1/canvas.py`
  - `app/backend/src/research_agent/application/dto/canvas.py`
  - `app/backend/src/research_agent/application/use_cases/canvas/` (new files)
  - `app/backend/src/research_agent/api/v1/websocket.py`

## Related Changes

- `unified-canvas-actions` - Frontend implementation (P0 complete)

