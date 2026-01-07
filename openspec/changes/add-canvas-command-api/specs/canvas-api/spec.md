# Canvas API Specification

## ADDED Requirements

### Requirement: Natural Language Command Understanding
The system SHALL convert natural language input into structured canvas actions using LLM function calling.

#### Scenario: Simple node creation
- **GIVEN** user input "Add a note about machine learning"
- **AND** canvas context with viewport center at (500, 400)
- **WHEN** NLU service processes the input
- **THEN** output action is `{ type: "addNode", payload: { content: "machine learning", x: 500, y: 400 } }`

#### Scenario: Pronoun resolution with selection
- **GIVEN** user input "Delete this"
- **AND** canvas context with selectedNodes = [{ id: "node-123", title: "Old Note" }]
- **WHEN** NLU service processes the input
- **THEN** output action is `{ type: "deleteNode", payload: { nodeId: "node-123" } }`

#### Scenario: Position inference from context
- **GIVEN** user input "Add a note here"
- **AND** selectedNodes = [{ id: "node-1", position: { x: 300, y: 200 } }]
- **WHEN** NLU service processes the input
- **THEN** new node is placed near selected node (e.g., x: 500, y: 200)

#### Scenario: Connect with implicit references
- **GIVEN** user input "Connect these two"
- **AND** selectedNodes = [{ id: "node-1" }, { id: "node-2" }]
- **WHEN** NLU service processes the input
- **THEN** output action is `{ type: "addEdge", payload: { source: "node-1", target: "node-2" } }`

#### Scenario: Color attribute extraction
- **GIVEN** user input "Create a yellow sticky note about deadlines"
- **WHEN** NLU service processes the input
- **THEN** output action includes `{ color: "yellow", content: "deadlines" }`

#### Scenario: Generation command understanding
- **GIVEN** user input "Generate a mindmap from my documents"
- **AND** availableDocuments = [{ id: "doc-1", title: "Research Paper" }]
- **WHEN** NLU service processes the input
- **THEN** output action is `{ type: "generateContent", payload: { contentType: "mindmap" } }`

#### Scenario: Synthesis command with mode
- **GIVEN** user input "Find connections between these ideas"
- **AND** selectedNodes contains 3 nodes
- **WHEN** NLU service processes the input
- **THEN** output action is `{ type: "synthesizeNodes", payload: { nodeIds: [...], mode: "connect" } }`

### Requirement: Canvas Context for LLM
The system SHALL build a context object containing canvas state for LLM inference.

#### Scenario: Context includes selected nodes
- **GIVEN** user has selected 2 nodes on canvas
- **WHEN** context is built for LLM
- **THEN** context.selectedNodes contains both nodes with id, title, contentPreview, position

#### Scenario: Context includes viewport
- **GIVEN** user has zoomed and panned the canvas
- **WHEN** context is built for LLM
- **THEN** context.viewport contains x, y, scale, and visibleBounds

#### Scenario: Context includes available documents
- **GIVEN** project has 3 uploaded documents
- **WHEN** context is built for LLM
- **THEN** context.availableDocuments contains id, title, type for each document

#### Scenario: Context size limit
- **GIVEN** canvas has 100+ nodes
- **WHEN** context is built for LLM
- **THEN** only selectedNodes and last 5 recentNodes are included (to limit token usage)

### Requirement: LLM Tool Calling Schema
The system SHALL define structured tool schemas for LLM function calling.

#### Scenario: Tool validation
- **GIVEN** LLM returns `{ tool: "addNode", parameters: { content: "test" } }`
- **WHEN** response is validated
- **THEN** validation passes (content is required, position is optional)

#### Scenario: Invalid tool parameters
- **GIVEN** LLM returns `{ tool: "connect", parameters: { sourceNodeId: "node-1" } }`
- **WHEN** response is validated
- **THEN** validation fails (targetNodeId is required)

#### Scenario: Non-existent node reference
- **GIVEN** LLM returns `{ tool: "deleteNode", parameters: { nodeId: "invalid-id" } }`
- **AND** canvas does not contain "invalid-id"
- **WHEN** action is validated against canvas state
- **THEN** error is returned: "Node not found: invalid-id"

### Requirement: Edge CRUD Operations
The system SHALL provide REST API endpoints for creating, updating, and deleting canvas edges (connections between nodes).

#### Scenario: Create edge between two nodes
- **GIVEN** a project with existing nodes "node-1" and "node-2"
- **WHEN** POST request to `/projects/{id}/canvas/edges` with `{ source: "node-1", target: "node-2", label: "supports" }`
- **THEN** a new edge is created and stored in canvas data
- **AND** response contains `edgeId` and new canvas `version`

#### Scenario: Create edge with invalid source
- **GIVEN** a project with node "node-1" but no "node-999"
- **WHEN** POST request to create edge from "node-1" to "node-999"
- **THEN** return 400 Bad Request with error "Source or target node not found"

#### Scenario: Update edge label
- **GIVEN** an existing edge "edge-1" with label "supports"
- **WHEN** PUT request to `/projects/{id}/canvas/edges/edge-1` with `{ label: "contradicts" }`
- **THEN** edge label is updated
- **AND** canvas version is incremented

#### Scenario: Delete edge
- **GIVEN** an existing edge "edge-1"
- **WHEN** DELETE request to `/projects/{id}/canvas/edges/edge-1`
- **THEN** edge is removed from canvas data
- **AND** response contains success and new version

### Requirement: Batch Node Operations
The system SHALL provide API endpoints for batch operations on multiple nodes.

#### Scenario: Delete multiple nodes
- **GIVEN** a project with nodes "node-1", "node-2", "node-3" and edges connecting them
- **WHEN** POST request to `/projects/{id}/canvas/nodes/batch-delete` with `{ nodeIds: ["node-1", "node-2"] }`
- **THEN** both nodes are deleted
- **AND** all edges connected to deleted nodes are also deleted
- **AND** response contains `deletedCount` and `deletedEdgeCount`

#### Scenario: Delete with invalid node ID
- **GIVEN** a project without "node-999"
- **WHEN** POST request to batch-delete with `{ nodeIds: ["node-999"] }`
- **THEN** operation succeeds with `deletedCount: 0` (idempotent)

### Requirement: Unified Action Endpoint
The system SHALL provide a unified endpoint for executing canvas actions programmatically.

#### Scenario: Execute addNode action
- **GIVEN** a project canvas
- **WHEN** POST request to `/projects/{id}/canvas/actions` with `{ type: "addNode", payload: { content: "Test", x: 100, y: 200 } }`
- **THEN** a new node is created at position (100, 200)
- **AND** response contains action result with `nodeId`

#### Scenario: Execute unknown action type
- **GIVEN** a project canvas
- **WHEN** POST request with `{ type: "unknownAction", payload: {} }`
- **THEN** return 400 Bad Request with "Unknown action type"

#### Scenario: Execute synthesizeNodes action
- **GIVEN** a project with nodes containing text content
- **WHEN** POST request with `{ type: "synthesizeNodes", payload: { nodeIds: [...], mode: "connect" } }`
- **THEN** AI synthesis is triggered asynchronously
- **AND** response contains `taskId` for tracking

### Requirement: Content Generation API
The system SHALL provide API endpoints for AI-powered content generation on the canvas.

#### Scenario: Generate mindmap from documents
- **GIVEN** a project with uploaded documents
- **WHEN** POST request to `/projects/{id}/canvas/generate` with `{ contentType: "mindmap" }`
- **THEN** mindmap generation task is queued
- **AND** response contains `taskId` and `status: "queued"`

#### Scenario: Generate with position
- **GIVEN** a project with documents
- **WHEN** POST request with `{ contentType: "summary", position: { x: 500, y: 300 } }`
- **THEN** generated content is placed at specified position

#### Scenario: Synthesize selected nodes
- **GIVEN** a project with nodes "node-1" (content A) and "node-2" (content B)
- **WHEN** POST request to `/projects/{id}/canvas/synthesize` with `{ nodeIds: ["node-1", "node-2"], mode: "connect" }`
- **THEN** AI analyzes both nodes and creates synthesis result
- **AND** new insight node is created on canvas

### Requirement: Action History Support
The system SHALL maintain action history to support undo/redo operations.

#### Scenario: Store action in history
- **GIVEN** an empty canvas action history
- **WHEN** user adds a node via action endpoint
- **THEN** action is added to undo stack
- **AND** redo stack is cleared

#### Scenario: Undo last action
- **GIVEN** action history with "addNode" action
- **WHEN** POST request to `/projects/{id}/canvas/undo`
- **THEN** the added node is removed
- **AND** action is moved to redo stack

#### Scenario: Redo undone action
- **GIVEN** an action in redo stack
- **WHEN** POST request to `/projects/{id}/canvas/redo`
- **THEN** action is re-applied
- **AND** action is moved back to undo stack

#### Scenario: History limit
- **GIVEN** undo stack with 50 actions
- **WHEN** new action is performed
- **THEN** oldest action is removed from stack
- **AND** new action is added (FIFO)

### Requirement: Real-time Action Sync
The system SHALL broadcast canvas actions to connected clients for real-time synchronization.

#### Scenario: Broadcast action to clients
- **GIVEN** multiple clients connected to project WebSocket
- **WHEN** one client executes a canvas action
- **THEN** all other clients receive `canvas_action` event
- **AND** event contains action type and result

#### Scenario: Client applies remote action
- **GIVEN** client receives `canvas_action` event with `{ type: "addNode", result: { nodeId: "..." } }`
- **WHEN** client processes the event
- **THEN** client updates local canvas state
- **AND** no duplicate API call is made

### Requirement: Edge Relation Types
The system SHALL support semantic relation types for edges to represent different relationships.

#### Scenario: Create edge with relation type
- **GIVEN** two nodes representing different concepts
- **WHEN** creating edge with `{ relationType: "contradicts" }`
- **THEN** edge is stored with relation type metadata
- **AND** frontend can display appropriate styling

#### Scenario: Valid relation types
The following relation types SHALL be supported:
- `supports` - Source supports/reinforces target
- `contradicts` - Source contradicts/opposes target
- `related` - Generic relationship
- `causes` - Source causes/leads to target
- `example` - Source is an example of target

## Data Structures

### CanvasContext (for LLM)
```python
class CanvasContext:
    # Selection state
    selectedNodeIds: list[str]
    selectedNodes: list[SelectedNodeInfo]  # id, title, contentPreview, position, color
    
    # Viewport state
    viewport: ViewportInfo            # x, y, scale, visibleBounds
    
    # Recent activity
    recentNodes: list[NodeSummary]    # Last 5 nodes (id, title)
    
    # Document context
    availableDocuments: list[DocumentInfo]  # id, title, type
    
    # Canvas stats
    totalNodes: int
    totalEdges: int
```

### LLMToolCall (response from LLM)
```python
class LLMToolCall:
    tool: str                        # Tool name (addNode, connect, etc.)
    parameters: dict                 # Tool-specific parameters
    reasoning: Optional[str]         # LLM's reasoning (for debugging)
```

### NLUResult
```python
class NLUResult:
    success: bool
    action: Optional[CanvasAction]   # Parsed action if successful
    error: Optional[str]             # Error message if failed
    confidence: float                # LLM confidence (0-1)
    requiresConfirmation: bool       # True for destructive actions
```

### EdgeDTO
```python
class CanvasEdgeDTO:
    id: str                          # Unique edge ID
    source: str                      # Source node ID
    target: str                      # Target node ID
    label: Optional[str]             # Human-readable label
    relationType: Optional[str]      # Semantic type (supports, contradicts, etc.)
```

### ActionRequest
```python
class CanvasActionRequest:
    type: str                        # Action type (addNode, deleteNode, etc.)
    payload: dict                    # Action-specific payload
```

### ActionHistoryEntry
```python
class ActionHistoryEntry:
    action: CanvasActionRequest      # The action performed
    timestamp: datetime              # When action was performed
    reversible: bool                 # Whether action can be undone
    inverseAction: Optional[dict]    # Action to reverse this one
```

## LLM Tool Definitions

### Supported Tools
| Tool | Description | Required Params | Optional Params |
|------|-------------|-----------------|-----------------|
| `addNode` | Create a new node | content | title, x, y, color |
| `updateNode` | Update node content | nodeId | content, title, color |
| `deleteNodes` | Delete node(s) | nodeIds | - |
| `moveNode` | Move node position | nodeId, x, y | - |
| `connect` | Create edge | sourceNodeId, targetNodeId | label, relationType |
| `disconnect` | Delete edge | edgeId | - |
| `generate` | Generate AI content | contentType | documentIds, position |
| `synthesize` | Synthesize nodes | nodeIds, mode | - |
| `search` | Find nodes (query) | query | limit |

### Relation Types
| Type | Description | Visual |
|------|-------------|--------|
| `supports` | Source reinforces target | Green arrow |
| `contradicts` | Source opposes target | Red dashed arrow |
| `related` | Generic relationship | Gray arrow |
| `causes` | Source leads to target | Blue arrow |
| `example` | Source exemplifies target | Purple arrow |

### Synthesis Modes
| Mode | Description | Output |
|------|-------------|--------|
| `connect` | Find relationships between nodes | Insight node with connections |
| `inspire` | Generate new ideas from nodes | Multiple new idea nodes |
| `debate` | Find tensions/contradictions | Debate summary node |

