# Capability: mindmap-navigation

## ADDED Requirements

### Requirement: Mindmap Visibility Control
The system SHALL allow users to toggle the visibility of node subtrees.

#### Scenario: User collapses a node
- **Given** a mindmap with a parent node A and child node B
- **When** the user clicks the collapse button on node A
- **Then** node B and any of its descendants SHALL be hidden from the view
- **And** all edges connected to hidden nodes SHALL be hidden
- **And** node A SHALL display an expand indicator (+)

#### Scenario: User expands a node
- **Given** a mindmap where node A is collapsed and its subtree is hidden
- **When** the user clicks the expand button on node A
- **Then** its immediate children SHALL be visible (unless they are also collapsed)
- **And** node A SHALL display a collapse indicator (-)
