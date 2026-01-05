# Specification: Studio UX

## Summary
Refines the Studio interface to resolve consistency and safety issues found in design review.

## ADDED Requirements

### Requirement: Header Context
The Studio header MUST display the human-readable Project Name.

#### Scenario: Opening a project
Given a project named "Mars Research"
When opening the Studio
Then the header displays "Mars Research" (not "Project 1234...")

---

### Requirement: Safe Deletion
There MUST NOT be a persistent floating action button for deletion.

#### Scenario: Deleting a node
Given a selected node
When the user wants to delete it
Then they use the Keyboard Shortcut (Del) OR a specific Context Menu/Toolbar action
And they do not see a giant trash can icon constantly on screen

---

### Requirement: Tool Grouping
Interaction tools (Select, Hand) MUST be visually distinct from View controls (Zoom).

#### Scenario: Switching tools
Given the user wants to pan
When they look for the Hand tool
Then it is located in a dedicated "Tools" group, separate from "Zoom In/Out"
