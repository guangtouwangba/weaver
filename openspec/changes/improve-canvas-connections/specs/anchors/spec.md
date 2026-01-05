# Spec: Connection Anchors

## ADDED Requirements

### Requirement: Anchor Types
The system SHALL support both Fixed (N/S/E/W) and Auto-selected anchors.

#### Scenario: Automatic anchor selection
- **Given** Node A is positioned to the left of Node B
- **When** the user creates a connection without specifying anchors
- **Then** the system should auto-select the East anchor of A and West anchor of B.

### Requirement: Anchor Visualization
The system SHALL visually indicate available anchor points when a user is creating or modifying a connection.

#### Scenario: Hovering over node displays anchors
- **Given** a node on the canvas
- **When** the user hovers over the node with a connection tool or creating a link
- **Then** the available anchor points (N, S, E, W) should be highlighted.
