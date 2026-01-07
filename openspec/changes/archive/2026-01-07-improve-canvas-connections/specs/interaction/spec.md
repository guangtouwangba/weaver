# Spec: Connection Interaction

## ADDED Requirements

### Requirement: Reconnection
The system SHALL allow users to change the source or target of an existing connection by dragging its endpoints.

#### Scenario: User reconnects an edge
- **Given** an edge from Node A to Node B
- **When** the user drags the target endpoint from Node B to Node C
- **Then** the edge should disconnect from B and connect to C.

### Requirement: Connection Labels
The system SHALL allow users to add text labels to connections.

#### Scenario: User adds label to edge
- **Given** an existing connection
- **When** the user inputs text for the connection label
- **Then** the text should appear along the connection path.

### Requirement: Deletion
The system SHALL allow users to delete selected connections.

#### Scenario: User deletes connection
- **Given** a selected connection
- **When** the user presses the Delete key
- **Then** the connection should be removed from the canvas.
