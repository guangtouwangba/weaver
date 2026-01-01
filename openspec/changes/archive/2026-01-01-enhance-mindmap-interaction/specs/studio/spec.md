# Specification Delta: Studio Module

## ADDED Requirements

### Requirement: Keyboard Shortcuts for Efficiency
Editor MUST support standard keyboard shortcuts to improve editing speed.

#### Scenario: Add Child Node
- **Given** a node is selected.
- **When** the user presses `Tab`.
- **Then** a new child node is created and selected.

#### Scenario: Add Sibling Node
- **Given** a node is selected (and is not Root).
- **When** the user presses `Enter`.
- **Then** a new sibling node is created and selected.

#### Scenario: Bulk Delete
- **Given** one or more nodes are selected.
- **When** the user presses `Delete`.
- **Then** all selected nodes and their descendants are deleted.
- **And** the action is recorded in history.

#### Scenario: Undo Operation
- **Given** the user has made changes (add/move/delete).
- **When** the user presses `Cmd+Z`.
- **Then** the state reverts to the previous version.

### Requirement: Multi-Selection and Bulk Actions
Editor MUST support selecting and manipulating multiple nodes simultaneously.

#### Scenario: Shift-Click Selection
- **Given** one node is already selected.
- **When** the user holds `Shift` and clicks another node.
- **Then** both nodes are selected.

#### Scenario: Rubber-band Selection
- **Given** no node is under the cursor.
- **When** the user drags on the canvas background.
- **Then** a selection rectangle appears.
- **And** all nodes intersecting the rectangle upon release are selected.

#### Scenario: Bulk Move
- **Given** multiple nodes are selected.
- **When** the user drags one of them.
- **Then** all selected nodes move by the same delta.
