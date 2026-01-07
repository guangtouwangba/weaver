# Design: Canvas Command API with Natural Language Understanding

## Context

The frontend `unified-canvas-actions` change implemented a slash command system. However, users shouldn't need to remember command syntax. The system should understand natural language like:

- "Add a sticky note about machine learning"
- "Connect these two ideas"
- "Generate a mindmap from my documents"
- "Delete the yellow notes"

This design covers both the NLU layer and the backend API.

**Stakeholders**: Solo developer (one-person company)
**Constraints**: Cost-conscious, prefer local processing, existing FastAPI + PostgreSQL stack

## Goals / Non-Goals

### Goals
- **NLU**: Convert natural language to structured canvas actions
- **Context-Aware**: Use canvas state to infer parameters
- **API**: Provide REST endpoints for all canvas operations
- **AI Generation**: Support mindmap, summary, synthesis commands
- **History**: Store action log for undo/redo

### Non-Goals
- Voice input - text only for now
- Multi-language support - English only initially
- Collaborative editing - single user focus
- Complex conflict resolution - last-write-wins acceptable

## Decisions

### 0. Natural Language Understanding Architecture

**Decision**: Hybrid approach - LLM function calling + rule-based fallback

```
User Input: "Add a yellow note about quantum computing near the selected node"
                                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Context Builder                              │
│  - Selected nodes: [node-123]                                   │
│  - Selected node position: (500, 300)                           │
│  - Viewport: { x: 0, y: 0, scale: 1 }                          │
│  - Recent nodes: [node-120, node-121, node-122]                │
└─────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Function Calling                         │
│  System: "You are a canvas assistant. Use these tools..."      │
│  Tools: [addNode, deleteNode, connect, generate, ...]          │
│  Context: { selectedNodes, viewport, recentNodes }             │
│                                                                 │
│  Output: {                                                      │
│    "tool": "addNode",                                          │
│    "parameters": {                                             │
│      "content": "quantum computing",                           │
│      "color": "yellow",                                        │
│      "x": 700,  // near selected node (500 + offset)           │
│      "y": 300                                                  │
│    }                                                           │
│  }                                                             │
└─────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Action Validator                             │
│  - Validate parameters against schema                          │
│  - Check node IDs exist                                        │
│  - Clamp positions to valid range                              │
└─────────────────────────────────────────────────────────────────┘
                                    ↓
                          Execute Action
```

**Rationale**:
- LLM handles ambiguity and natural language variation
- Function calling ensures structured output
- Context injection enables smart parameter inference
- Validation layer catches LLM errors

**Alternatives considered**:
- Pure rule-based NLU: Too brittle for natural language variation
- Fine-tuned model: Expensive, hard to maintain
- Embedding similarity: Good for intent, bad for parameter extraction

### 0.1 Context Schema for LLM

```typescript
interface CanvasContext {
  // Selection state
  selectedNodeIds: string[];
  selectedNodes: Array<{
    id: string;
    title: string;
    contentPreview: string;  // First 100 chars
    position: { x: number; y: number };
    color: string;
  }>;
  
  // Viewport state
  viewport: {
    x: number;
    y: number;
    scale: number;
    visibleBounds: { minX, maxX, minY, maxY };
  };
  
  // Recent activity
  recentNodes: Array<{ id: string; title: string }>;  // Last 5
  
  // Document context
  availableDocuments: Array<{
    id: string;
    title: string;
    type: string;  // pdf, text, etc.
  }>;
  
  // Canvas stats
  totalNodes: number;
  totalEdges: number;
}
```

### 0.2 LLM Tool Definitions

```typescript
const canvasTools = [
  {
    name: "addNode",
    description: "Create a new note/card on the canvas",
    parameters: {
      type: "object",
      properties: {
        content: { 
          type: "string", 
          description: "The text content of the note" 
        },
        title: { 
          type: "string", 
          description: "Optional short title" 
        },
        x: { 
          type: "number", 
          description: "X position. Use context to place near relevant nodes" 
        },
        y: { 
          type: "number", 
          description: "Y position" 
        },
        color: { 
          type: "string", 
          enum: ["default", "yellow", "green", "blue", "red", "purple"],
          description: "Card color" 
        },
      },
      required: ["content"]
    }
  },
  {
    name: "connect",
    description: "Create a connection/edge between two nodes",
    parameters: {
      type: "object",
      properties: {
        sourceNodeId: { 
          type: "string", 
          description: "ID of source node. Use selectedNodes from context if user says 'this'" 
        },
        targetNodeId: { 
          type: "string", 
          description: "ID of target node" 
        },
        label: { 
          type: "string", 
          description: "Optional label for the connection" 
        },
        relationType: {
          type: "string",
          enum: ["supports", "contradicts", "related", "causes", "example"],
          description: "Semantic relationship type"
        }
      },
      required: ["sourceNodeId", "targetNodeId"]
    }
  },
  {
    name: "deleteNodes",
    description: "Delete one or more nodes from the canvas",
    parameters: {
      type: "object",
      properties: {
        nodeIds: {
          type: "array",
          items: { type: "string" },
          description: "IDs of nodes to delete. Use selectedNodes if user says 'delete this/these'"
        }
      },
      required: ["nodeIds"]
    }
  },
  {
    name: "generate",
    description: "Generate AI content (mindmap, summary, etc.) from documents",
    parameters: {
      type: "object",
      properties: {
        contentType: {
          type: "string",
          enum: ["mindmap", "summary", "flashcards", "action_list"],
          description: "Type of content to generate"
        },
        documentIds: {
          type: "array",
          items: { type: "string" },
          description: "Specific documents to use. Empty means all documents"
        },
        position: {
          type: "object",
          properties: { x: { type: "number" }, y: { type: "number" } },
          description: "Where to place generated content"
        }
      },
      required: ["contentType"]
    }
  },
  {
    name: "synthesize",
    description: "Analyze and synthesize insights from selected nodes",
    parameters: {
      type: "object",
      properties: {
        nodeIds: {
          type: "array",
          items: { type: "string" },
          description: "Nodes to synthesize. Use selectedNodes if user says 'synthesize these'"
        },
        mode: {
          type: "string",
          enum: ["connect", "inspire", "debate"],
          description: "Synthesis mode: connect (find relationships), inspire (generate ideas), debate (find tensions)"
        }
      },
      required: ["nodeIds", "mode"]
    }
  },
  {
    name: "search",
    description: "Find nodes matching a query (not an action, returns results)",
    parameters: {
      type: "object",
      properties: {
        query: { type: "string", description: "Search query" },
        limit: { type: "number", description: "Max results to return" }
      },
      required: ["query"]
    }
  }
];
```

### 0.3 System Prompt for Canvas Agent

```
You are a canvas assistant that helps users manipulate a visual thinking canvas.

You have access to tools for:
- Adding/deleting/updating nodes (cards/notes)
- Connecting nodes with edges
- Generating content from documents (mindmaps, summaries)
- Synthesizing insights from selected nodes

## Context Understanding

The user's canvas state is provided in the context:
- selectedNodes: What the user has currently selected
- viewport: What area is visible
- recentNodes: Recently created/modified nodes
- availableDocuments: Documents that can be used for generation

## Pronoun Resolution

When the user says:
- "this" or "it" → Use the first selectedNode, or most recent node
- "these" → Use all selectedNodes
- "here" → Use viewport center or near selected nodes
- "the yellow ones" → Filter nodes by color from context

## Position Intelligence

When placing new nodes:
- If user specifies location ("top left", "near X") → calculate coordinates
- If nodes are selected → place new node nearby (offset by 200px)
- Default → place in viewport center

## Examples

User: "Add a note about quantum entanglement"
→ addNode({ content: "quantum entanglement", x: viewportCenterX, y: viewportCenterY })

User: "Connect these two ideas"
→ connect({ sourceNodeId: selectedNodes[0].id, targetNodeId: selectedNodes[1].id })

User: "Create a mindmap from my documents"
→ generate({ contentType: "mindmap", documentIds: [], position: viewportCenter })

User: "Delete the selected notes"
→ deleteNodes({ nodeIds: selectedNodes.map(n => n.id) })

User: "What's the relationship between these concepts?"
→ synthesize({ nodeIds: selectedNodes.map(n => n.id), mode: "connect" })
```

### 1. Edge Storage Strategy

**Decision**: Store edges as part of canvas JSON data (same as current approach)

**Rationale**: 
- Edges are already stored in `canvas.data['edges']` array
- No schema migration needed
- Atomic updates with nodes

**Alternatives considered**:
- Separate `canvas_edges` table - More normalized but adds complexity
- Graph database (Neo4j) - Overkill for current scale

### 2. Action Endpoint Design

**Decision**: Unified action endpoint + individual resource endpoints

```
# Individual endpoints (REST-ful, for simple operations)
POST   /projects/{id}/canvas/nodes           # Create node
PUT    /projects/{id}/canvas/nodes/{id}      # Update node
DELETE /projects/{id}/canvas/nodes/{id}      # Delete node
POST   /projects/{id}/canvas/edges           # Create edge
DELETE /projects/{id}/canvas/edges/{id}      # Delete edge

# Unified endpoint (for complex/batch operations)
POST   /projects/{id}/canvas/actions         # Execute any action
```

**Rationale**:
- REST endpoints are intuitive for simple CRUD
- Unified endpoint handles complex operations (batch, AI generation)
- Frontend can choose based on operation type

### 3. AI Generation Integration

**Decision**: Reuse existing `/chat` WebSocket streaming for generation commands

**Rationale**:
- Mindmap generation already uses streaming
- Consistent UX (user sees generation progress)
- No new infrastructure needed

**Flow**:
```
Frontend: /generate mindmap
→ Parse command, get CanvasAction { type: 'generateContent', payload: { contentType: 'mindmap' } }
→ Call existing generation API (POST /chat or WebSocket)
→ Stream results to canvas
```

### 4. Action History Schema

**Decision**: Store actions in canvas JSON data with limited history

```typescript
interface CanvasData {
  nodes: Node[];
  edges: Edge[];
  viewport: Viewport;
  // NEW: Action history
  actionHistory?: {
    undoStack: CanvasAction[];  // Max 50 actions
    redoStack: CanvasAction[];  // Cleared on new action
  };
}
```

**Rationale**:
- Simple implementation (no schema migration)
- History travels with canvas data
- Limit to 50 actions to control data size

**Alternatives considered**:
- Separate `canvas_action_history` table - More robust but adds complexity
- Event sourcing - Overkill for current needs

## API Specification

### Edge Endpoints

```python
# Create Edge
POST /projects/{project_id}/canvas/edges
Request:
{
  "source": "node-1",
  "target": "node-2",
  "label": "leads to",           # Optional
  "relationType": "supports"     # Optional: supports, contradicts, neutral
}
Response: { "success": true, "edgeId": "edge-xxx", "version": 5 }

# Update Edge
PUT /projects/{project_id}/canvas/edges/{edge_id}
Request:
{
  "label": "new label",
  "relationType": "contradicts"
}
Response: { "success": true, "version": 6 }

# Delete Edge
DELETE /projects/{project_id}/canvas/edges/{edge_id}
Response: { "success": true, "version": 7 }
```

### Batch Operations

```python
# Batch Delete Nodes
POST /projects/{project_id}/canvas/nodes/batch-delete
Request:
{
  "nodeIds": ["node-1", "node-2", "node-3"]
}
Response: { 
  "success": true, 
  "deletedCount": 3,
  "deletedEdgeCount": 2,  # Edges connected to deleted nodes
  "version": 8 
}
```

### Unified Action Endpoint

```python
# Execute Action
POST /projects/{project_id}/canvas/actions
Request:
{
  "type": "addNode",
  "payload": { "content": "New Note", "x": 100, "y": 200 }
}
# OR
{
  "type": "deleteNodes",
  "payload": { "nodeIds": ["node-1", "node-2"] }
}
# OR
{
  "type": "synthesizeNodes",
  "payload": { "nodeIds": ["node-1", "node-2"], "mode": "connect" }
}
Response: {
  "success": true,
  "result": { ... },  # Action-specific result
  "version": 9
}
```

### Generation Endpoints

```python
# Generate Content (triggers streaming via existing infrastructure)
POST /projects/{project_id}/canvas/generate
Request:
{
  "contentType": "mindmap" | "summary" | "flashcards" | "action_list",
  "position": { "x": 100, "y": 200 },  # Optional: where to place result
  "sourceDocuments": ["doc-1", "doc-2"]  # Optional: specific docs
}
Response: {
  "taskId": "task-xxx",  # Poll or use WebSocket for results
  "status": "queued"
}

# Synthesize Nodes
POST /projects/{project_id}/canvas/synthesize
Request:
{
  "nodeIds": ["node-1", "node-2"],
  "mode": "connect" | "inspire" | "debate"
}
Response: {
  "taskId": "task-xxx",
  "status": "queued"
}
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Data size growth with action history | Limit to 50 actions, prune on save |
| Concurrent edit conflicts | Version check + last-write-wins (acceptable for single user) |
| Complex action reversal | Start with simple actions, add complex undo later |

## Migration Plan

1. **Phase 1 (P0)**: Add edge endpoints, batch delete - No schema changes
2. **Phase 2 (P1)**: Add unified action endpoint, generation endpoints
3. **Phase 3 (P2)**: Add action history, WebSocket sync

**Rollback**: All changes are additive. Existing API unchanged.

## Open Questions

1. Should action history be stored in separate table for better querying?
2. How to handle long-running generation tasks (timeout? cancellation?)
3. Should we add rate limiting for action endpoints?

