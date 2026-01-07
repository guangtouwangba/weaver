# Specification: Canvas Actions

## Summary

Defines a unified action system for programmatic canvas manipulation. All canvas operations are expressed as typed actions that can be dispatched, logged, and reversed.

## Requirements

### Requirement: Action Type Definition
All canvas operations MUST be represented as discriminated union types.

#### Scenario: Adding a node via action
Given a dispatch function
When `dispatch({ type: 'addNode', payload: { type: 'sticky', x: 100, y: 100, content: 'New' } })` is called
Then a new sticky node appears at position (100, 100)

#### Scenario: Deleting multiple nodes
Given selected node IDs `['node-1', 'node-2']`
When `dispatch({ type: 'deleteNodes', payload: { nodeIds: ['node-1', 'node-2'] } })` is called
Then both nodes and their connected edges are removed

---

### Requirement: Action Dispatcher Hook
A `useCanvasDispatch` hook MUST be provided for executing actions.

#### Scenario: Dispatching from any component
Given a component using `useCanvasDispatch`
When an action is dispatched
Then the canvas state updates accordingly

---

### Requirement: Batch Actions
Multiple actions SHOULD be batchable into a single operation.

#### Scenario: Creating a node with edges
Given an action batch containing `addNode` and `addEdge`
When the batch is dispatched
Then all operations apply atomically

---

### Requirement: Edge Actions
The action system MUST support all edge (connection) operations for creating, updating, and deleting relationships between nodes.

#### Scenario: Creating an edge between two nodes
- **WHEN** `dispatch({ type: 'addEdge', payload: { source: 'node-1', target: 'node-2', label: 'relates to' } })` is called
- **THEN** a new edge is created connecting node-1 to node-2
- **AND** the edge displays the label "relates to"

#### Scenario: Creating an edge with relation type
- **WHEN** `dispatch({ type: 'addEdge', payload: { source: 'node-1', target: 'node-2', relationType: 'leads_to' } })` is called
- **THEN** a new edge is created with the specified relation type
- **AND** the edge renders with the appropriate visual style for that relation

#### Scenario: Updating edge label
- **WHEN** `dispatch({ type: 'updateEdge', payload: { edgeId: 'edge-1', updates: { label: 'new label' } } })` is called
- **THEN** the edge label updates to "new label"

#### Scenario: Updating edge relation type
- **WHEN** `dispatch({ type: 'updateEdge', payload: { edgeId: 'edge-1', updates: { relationType: 'contradicts' } } })` is called
- **THEN** the edge relation type changes
- **AND** the visual style updates accordingly

#### Scenario: Deleting a single edge
- **WHEN** `dispatch({ type: 'deleteEdge', payload: { edgeId: 'edge-1' } })` is called
- **THEN** the edge is removed from the canvas
- **AND** the connected nodes remain unchanged

#### Scenario: Reconnecting an edge to a different target
- **WHEN** `dispatch({ type: 'reconnectEdge', payload: { edgeId: 'edge-1', newTarget: 'node-3' } })` is called
- **THEN** the edge's target changes from the original node to node-3
- **AND** duplicate edge validation is performed

#### Scenario: Preventing duplicate edges
- **GIVEN** an edge already exists between node-1 and node-2
- **WHEN** `dispatch({ type: 'addEdge', payload: { source: 'node-1', target: 'node-2' } })` is called
- **THEN** the action is rejected or ignored
- **AND** no duplicate edge is created

#### Scenario: Cascading edge deletion with node
- **WHEN** `dispatch({ type: 'deleteNode', payload: { nodeId: 'node-1' } })` is called
- **THEN** node-1 is removed
- **AND** all edges where node-1 is source or target are also removed

---

### Requirement: Selection Actions
The action system MUST support selection operations for nodes and edges.

#### Scenario: Selecting multiple nodes
- **WHEN** `dispatch({ type: 'selectNodes', payload: { nodeIds: ['node-1', 'node-2'] } })` is called
- **THEN** both nodes become selected
- **AND** previous selection is replaced

#### Scenario: Selecting an edge
- **WHEN** `dispatch({ type: 'selectEdge', payload: { edgeId: 'edge-1' } })` is called
- **THEN** the edge becomes selected with visual feedback
- **AND** any node selection is cleared

#### Scenario: Clearing all selection
- **WHEN** `dispatch({ type: 'clearSelection', payload: {} })` is called
- **THEN** all nodes and edges are deselected

#### Scenario: Select all nodes
- **WHEN** `dispatch({ type: 'selectAll', payload: {} })` is called
- **THEN** all visible nodes become selected

---

### Requirement: Viewport Actions
The action system MUST support viewport manipulation for navigation and zoom control.

#### Scenario: Pan to specific position
- **WHEN** `dispatch({ type: 'panTo', payload: { x: 500, y: 300 } })` is called
- **THEN** the viewport centers on the specified canvas coordinates

#### Scenario: Zoom to specific level
- **WHEN** `dispatch({ type: 'zoomTo', payload: { scale: 1.5 } })` is called
- **THEN** the viewport zoom level changes to 150%

#### Scenario: Zoom in by step
- **WHEN** `dispatch({ type: 'zoomIn', payload: {} })` is called
- **THEN** the viewport zoom increases by a predefined step (e.g., 20%)

#### Scenario: Fit all content in view
- **WHEN** `dispatch({ type: 'fitToContent', payload: {} })` is called
- **THEN** the viewport adjusts to show all nodes with padding

---

### Requirement: Slash Command Syntax
The action system MUST support a slash command syntax for human-readable and AI-parseable action invocation.

#### Scenario: Add node via slash command
- **WHEN** user types `/add-node "My Idea" --type sticky --color yellow`
- **THEN** a new sticky note is created at the current viewport center
- **AND** the node content is set to "My Idea"

#### Scenario: Add node with position
- **WHEN** user types `/add-node "Note" --at 100,200`
- **THEN** a new node is created at position (100, 200)

#### Scenario: Connect nodes via slash command
- **WHEN** user types `/connect node-1 node-2 --label "leads to"`
- **THEN** an edge is created between node-1 and node-2 with the specified label

#### Scenario: Connect with relation type
- **WHEN** user types `/connect node-1 node-2 --type contradicts`
- **THEN** an edge is created with the "contradicts" relation type and appropriate styling

#### Scenario: Delete via slash command
- **WHEN** user types `/delete node-1` or `/delete selected`
- **THEN** the specified node(s) are removed from the canvas

#### Scenario: Update node content
- **WHEN** user types `/update node-1 --content "Updated content"`
- **THEN** the node's content is updated

#### Scenario: Generate content via command
- **WHEN** user types `/generate mindmap` or `/generate summary`
- **THEN** the corresponding content generation is triggered

#### Scenario: Viewport commands
- **WHEN** user types `/zoom 150%` or `/zoom in` or `/fit`
- **THEN** the viewport adjusts accordingly

#### Scenario: Selection commands
- **WHEN** user types `/select all` or `/select node-1 node-2`
- **THEN** the specified nodes become selected

#### Scenario: Synthesize via command
- **WHEN** user types `/synthesize selected --mode connect`
- **THEN** the selected nodes are synthesized with the specified mode

#### Scenario: Command autocomplete
- **WHEN** user types `/` in the chat input
- **THEN** a command palette appears showing available commands
- **AND** commands are filtered as user continues typing

#### Scenario: Command help
- **WHEN** user types `/help` or `/help add-node`
- **THEN** help information for available commands or the specific command is displayed

---

### Requirement: Command Parser
The system MUST provide a parser that converts slash commands to action dispatches.

#### Scenario: Parse simple command
- **GIVEN** the command string `/add-node "My Note"`
- **WHEN** the parser processes it
- **THEN** it returns `{ type: 'addNode', payload: { content: 'My Note' } }`

#### Scenario: Parse command with flags
- **GIVEN** the command string `/connect node-1 node-2 --label "relates to" --type causal`
- **WHEN** the parser processes it
- **THEN** it returns `{ type: 'addEdge', payload: { source: 'node-1', target: 'node-2', label: 'relates to', relationType: 'causal' } }`

#### Scenario: Handle invalid command
- **GIVEN** an invalid command string `/unknowncommand`
- **WHEN** the parser processes it
- **THEN** it returns an error with suggestions for similar valid commands

#### Scenario: AI-generated commands
- **WHEN** the AI agent generates a response with canvas actions
- **THEN** it outputs actions as slash commands that can be executed
- **AND** the user can review and confirm before execution

---

## Slash Command Reference

| Command | Syntax | Description |
|---------|--------|-------------|
| `/add-node` | `/add-node "content" [--type TYPE] [--at X,Y] [--color COLOR]` | Create a new node |
| `/delete` | `/delete NODE_ID \| selected` | Delete node(s) |
| `/update` | `/update NODE_ID --content "text" \| --title "text"` | Update node properties |
| `/move` | `/move NODE_ID --to X,Y` | Move node to position |
| `/connect` | `/connect SOURCE TARGET [--label TEXT] [--type TYPE]` | Create edge between nodes |
| `/disconnect` | `/disconnect EDGE_ID \| SOURCE TARGET` | Remove edge |
| `/select` | `/select NODE_IDS... \| all \| none` | Set selection |
| `/zoom` | `/zoom LEVEL \| in \| out \| fit` | Adjust viewport zoom |
| `/pan` | `/pan X,Y \| to NODE_ID` | Pan viewport |
| `/generate` | `/generate TYPE [--at X,Y]` | Generate content (mindmap, summary, etc.) |
| `/synthesize` | `/synthesize selected --mode MODE` | Synthesize selected nodes |
| `/help` | `/help [COMMAND]` | Show help information |

### Command Flags

| Flag | Alias | Description |
|------|-------|-------------|
| `--type` | `-t` | Node type or edge relation type |
| `--at` | `-a` | Position as X,Y coordinates |
| `--to` | | Target position for move/pan |
| `--color` | `-c` | Node color |
| `--label` | `-l` | Edge label text |
| `--content` | | Node content |
| `--title` | | Node title |
| `--mode` | `-m` | Synthesis mode (connect, inspire, debate) |

---

## Action Types Reference

### Node Actions
| Action Type | Payload | Description |
|-------------|---------|-------------|
| `addNode` | `Partial<CanvasNode>` | Creates a new node |
| `updateNode` | `{ nodeId, updates }` | Updates node properties |
| `deleteNode` | `{ nodeId }` | Removes a node and its edges |
| `deleteNodes` | `{ nodeIds }` | Removes multiple nodes and their edges |
| `moveNode` | `{ nodeId, x, y }` | Changes node position |

### Edge Actions
| Action Type | Payload | Description |
|-------------|---------|-------------|
| `addEdge` | `{ source, target, label?, relationType? }` | Creates a connection between nodes |
| `updateEdge` | `{ edgeId, updates }` | Updates edge label or relation type |
| `deleteEdge` | `{ edgeId }` | Removes a connection |
| `reconnectEdge` | `{ edgeId, newSource?, newTarget? }` | Moves edge endpoint to different node |

### Selection Actions
| Action Type | Payload | Description |
|-------------|---------|-------------|
| `selectNodes` | `{ nodeIds }` | Sets node selection |
| `selectEdge` | `{ edgeId }` | Selects a single edge |
| `clearSelection` | `{}` | Clears all selection |
| `selectAll` | `{}` | Selects all visible nodes |

### Viewport Actions
| Action Type | Payload | Description |
|-------------|---------|-------------|
| `panTo` | `{ x, y }` | Pans viewport to position |
| `zoomTo` | `{ scale }` | Sets zoom level |
| `zoomIn` | `{}` | Increases zoom by step |
| `zoomOut` | `{}` | Decreases zoom by step |
| `fitToContent` | `{}` | Fits all nodes in view |

### Generation Actions
| Action Type | Payload | Description |
|-------------|---------|-------------|
| `synthesizeNodes` | `{ nodeIds, mode }` | Synthesizes selected nodes into insight |
| `generateContent` | `{ type, position }` | Triggers content generation at position |

