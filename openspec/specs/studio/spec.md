# studio Specification

## Purpose
TBD - created by archiving change add-document-summary. Update Purpose after archive.
## Requirements
### Requirement: Document Selection State
The Resource Sidebar SHALL provide visual feedback when documents are selected.

#### Scenario: Active document styling
- **WHEN** a user clicks a document card
- **THEN** the card border becomes highlighted (e.g., primary color)
- **AND** the background color changes to indicate selection

### Requirement: Inspiration Dock Summary Action
The Inspiration Dock SHALL offer a mechanism to trigger summarization.

#### Scenario: Summarize button availability
- **WHEN** one or more documents are selected in the sidebar
- **THEN** the Inspiration Dock displays a "Summarize" option/icon

### Requirement: Summary Card Display
The system SHALL display the generated summary in a dedicated card format.

#### Scenario: Summary presentation
- **WHEN** the summary generation is complete
- **THEN** a Summary Card appears containing:
  - A header with title and AI attribution
  - Tags (e.g., STRATEGY, INSIGHTS)
  - A brief narrative text
  - A highlights section with key metrics or points
  - A "Read Full Summary" action

#### Scenario: Full content expansion
- **WHEN** the user selects "Read Full Summary"
- **THEN** the card expands or opens a modal to show the complete detailed summary

### Requirement: Inspiration Dock Visibility Control
The system MUST allow users to toggle the visibility of the Inspiration Dock.

#### Scenario: Closing the Dock
- **WHEN** the user clicks the "Close" (X) button on the Inspiration Dock
- **THEN** the Inspiration Dock disappears from the view
- **AND** a "Sparkles" icon/toggle becomes available/highlighted in the toolbar

#### Scenario: Re-opening the Dock
- **WHEN** the Inspiration Dock is hidden
- **AND** the user clicks the "Sparkles" toggle in the toolbar
- **THEN** the Inspiration Dock reappears in the center of the screen

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

