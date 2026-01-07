# Spec: Connection Routing

## ADDED Requirements

### Requirement: Routing Types
The system SHALL support multiple routing algorithms for connections: Straight and Orthogonal.

#### Scenario: User selects straight routing
- **Given** two nodes connected by an edge
- **When** the user selects "Straight" routing type
- **Then** the edge should be rendered as a straight line between the source and target anchors.

#### Scenario: User selects orthogonal routing
- **Given** two nodes connected by an edge
- **When** the user selects "Orthogonal" routing type
- **Then** the edge should be rendered using only horizontal and vertical segments.

### Requirement: Obstacle Avoidance
The system SHALL attempt to route orthogonal connections around obstacles (other nodes) where possible.

#### Scenario: Orthogonal routing avoids obstacles
- **Given** Node A, Node B, and Node C positioned directly between them
- **When** the user creates an orthogonal connection from A to B
- **Then** the path should route around Node C, not through it.
