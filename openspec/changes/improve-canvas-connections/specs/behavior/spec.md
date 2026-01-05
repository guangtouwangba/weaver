# Spec: Connection Behavior

## ADDED Requirements

### Requirement: Follow Movement
The system SHALL update connection paths automatically when connected nodes are moved.

#### Scenario: Edge follows node movement
- **Given** an edge connecting Node A and Node B
- **When** the user drags Node A to a new position
- **Then** the edge should remain connected and update its path to valid anchors.

### Requirement: Self-Connection
The system SHALL support connecting a node to itself (Loop).

#### Scenario: User creates self-loop
- **Given** a node
- **When** the user connects the node's Top anchor to its Right anchor
- **Then** a loop connection should be created.
