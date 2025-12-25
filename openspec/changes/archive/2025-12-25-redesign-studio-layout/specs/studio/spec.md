## ADDED Requirements

### Requirement: Studio Layout
The Studio SHALL provide a workspace centered around an infinite whiteboard canvas.

#### Scenario: Default layout
- **WHEN** a user opens a project
- **THEN** they see the whiteboard canvas occupying the majority of the screen
- **AND** a resource sidebar on the left
- **AND** floating controls for chat and navigation overlaid on the canvas.

### Requirement: Resource Management
The Studio SHALL provide a dedicated sidebar for managing project resources.

#### Scenario: File upload
- **WHEN** a user drags a file onto the "Drop files here" zone in the sidebar
- **THEN** the file is uploaded and added to the resource list.

### Requirement: Canvas Interaction
The Studio SHALL provide high-performance canvas interactions.

#### Scenario: Navigation
- **WHEN** a user interacts with the floating navigation controls
- **THEN** the canvas zooms or pans accordingly with smooth transitions.

### Requirement: Floating Chat Interface
The Studio SHALL provide a floating chat interface for AI assistance.

#### Scenario: Chat interaction
- **WHEN** a user types in the bottom-center chat bar
- **THEN** the message is sent to the AI and the response is displayed contextually.
