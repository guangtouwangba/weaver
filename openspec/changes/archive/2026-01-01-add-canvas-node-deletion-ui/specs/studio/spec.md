# Studio

## ADDED Requirements

### Requirement: Canvas Node Management
The Studio Canvas SHALL allow users to create, edit, and delete nodes.

#### Scenario: Delete node via context menu
- **WHEN** a user right-clicks on a canvas node
- **AND** selects "Delete" from the context menu
- **THEN** the node SHALL be removed from the canvas
- **AND** the deletion SHALL be persisted to the backend
- **AND** a success toast notification SHALL appear

#### Scenario: Delete node via keyboard shortcut
- **WHEN** a user selects a canvas node
- **AND** presses the Delete or Backspace key
- **THEN** the selected node SHALL be removed from the canvas
- **AND** the deletion SHALL be persisted to the backend
- **AND** a success toast notification SHALL appear

#### Scenario: Delete generated content
- **WHEN** AI generates a mindmap or summary node on the canvas
- **AND** the content contains errors
- **THEN** the user SHALL be able to delete the generated node using either context menu or keyboard
- **AND** the canvas workspace SHALL remain clean

#### Scenario: Handle deletion failures
- **WHEN** node deletion fails due to network error or conflict
- **THEN** an error toast SHALL be displayed
- **AND** the node SHALL remain on the canvas (optimistic update rollback)
