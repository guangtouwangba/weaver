# Spec: Split View Workspace

## ADDED Requirements

### Requirement: Split View Grid Layout
The Studio interface MUST support a 3-pane layout allowing simultaneous visibility of the Resource Sidebar, Content Viewer, and Mindmap Canvas.

#### Scenario: Opening the Studio
- **Given** I am on the Studio page.
- **When** the page loads.
- **Then** I should see the Resource Sidebar on the left.
- **And** the Mindmap Canvas in the center/right.
- **And** the Content Panel should be hidden or collapsed initially.

### Requirement: Content Docking
When a user opens a document or video, it MUST open in the docked Content Panel instead of a modal overlay.

#### Scenario: Opening a PDF
- **Given** the Split View layout is active.
- **When** I click a PDF file in the Resource Sidebar.
- **Then** the Content Panel should expand between the Sidebar and Canvas.
- **And** the PDF should be rendered within this panel.
- **And** the Mindmap Canvas should resize to fill the remaining space.

### Requirement: Persistent Panel Resizing
Users MUST be able to resize the Content Panel width, and this preference should be persisted.

#### Scenario: Resizing the panel
- **Given** the Content Panel is open.
- **When** I drag the handle between the Content Panel and Canvas.
- **Then** the panels should resize smoothly.
- **And** the new width should be saved for my next session.
