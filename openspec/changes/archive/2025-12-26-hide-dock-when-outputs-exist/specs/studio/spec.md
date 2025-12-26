## MODIFIED Requirements

### Requirement: Inspiration Dock Visibility Control
The system MUST allow users to toggle the visibility of the Inspiration Dock.
The Inspiration Dock SHALL automatically hide when outputs already exist on the canvas.

#### Scenario: Closing the Dock
- **WHEN** the user clicks the "Close" (X) button on the Inspiration Dock
- **THEN** the Inspiration Dock disappears from the view
- **AND** a "Sparkles" icon/toggle becomes available/highlighted in the toolbar


#### Scenario: Auto-hide when outputs exist
- **WHEN** the canvas has one or more completed generation outputs (e.g., mindmap, summary)
- **THEN** the Inspiration Dock SHALL NOT be displayed
- **AND** users can generate additional content via the right-click context menu

#### Scenario: Show dock on empty canvas with documents
- **WHEN** the canvas has no generation outputs
- **AND** one or more documents are uploaded
- **THEN** the Inspiration Dock is displayed as the primary entry point for generation

## ADDED Requirements

### Requirement: Right-Click Context Menu Generation
The canvas context menu SHALL provide content generation options that place outputs at the right-click position.

#### Scenario: Generate mindmap via context menu
- **WHEN** a user right-clicks on the canvas
- **AND** selects "Generate Mind Map" from the context menu
- **THEN** the mindmap generation starts
- **AND** the generated mindmap appears as a canvas node at the right-click position

#### Scenario: Generate summary via context menu
- **WHEN** a user right-clicks on the canvas
- **AND** selects "Generate Summary" from the context menu
- **THEN** the summary generation starts
- **AND** the generated summary appears as a canvas node at the right-click position

#### Scenario: Context menu available when dock is hidden
- **WHEN** the Inspiration Dock is hidden (either manually or due to existing outputs)
- **THEN** the right-click context menu remains the primary method for generating content
