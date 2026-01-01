## ADDED Requirements

### Requirement: Mind Map Persistence
The system MUST allow users to save changes made to generated mind maps so that edits are preserved across sessions.

#### Scenario: User edits a mind map node
- **Given** a generated mind map is open on the canvas.
- **When** the user edits a node's label or content and saves the node.
- **Then** the updated mind map data is sent to the backend and persisted.
- **And** reloading the page restores the mind map with the user's edits.

#### Scenario: User adds a new node
- **Given** a generated mind map.
- **When** the user adds a new child node in the editor.
- **Then** the new node structure is persisted to the backend.

#### Scenario: User deletes a node
- **Given** a generated mind map.
- **When** the user deletes a node (and its connection).
- **Then** the removal is persisted.
