## MODIFIED Requirements

### Requirement: Canvas Interaction
The Studio SHALL provide high-performance canvas interactions.

#### Scenario: Navigation
- **WHEN** a user interacts with the floating navigation controls
- **THEN** the canvas zooms or pans accordingly with smooth transitions.

#### Scenario: Pan mode with hand tool
- **WHEN** the user selects the hand tool from the toolbar or presses 'H' key
- **AND** clicks and drags on the canvas
- **THEN** the canvas viewport SHALL pan in the direction of the drag
- **AND** node selection SHALL NOT occur
- **AND** nodes SHALL NOT be draggable while hand tool is active

#### Scenario: Pan mode with spacebar
- **WHEN** the user holds the spacebar key
- **AND** clicks and drags on the canvas
- **THEN** the canvas viewport SHALL pan in the direction of the drag
- **AND** this SHALL work regardless of the currently selected tool

### Requirement: Right-Click Context Menu Generation
The canvas context menu SHALL provide content generation options that place outputs at the right-click position.

#### Scenario: Generate mindmap via context menu
- **WHEN** a user right-clicks on the canvas
- **AND** selects "Generate Mind Map" from the context menu
- **THEN** the mindmap generation starts
- **AND** a loading placeholder card SHALL appear immediately at the click position
- **AND** the placeholder SHALL display a spinner with "Generating..." text
- **AND** the generated mindmap replaces the placeholder when complete

#### Scenario: Generate summary via context menu
- **WHEN** a user right-clicks on the canvas
- **AND** selects "Generate Summary" from the context menu
- **THEN** the summary generation starts
- **AND** a loading placeholder card SHALL appear immediately at the click position
- **AND** the placeholder SHALL display a spinner with "Generating..." text
- **AND** the generated summary replaces the placeholder when complete

#### Scenario: Consistent feedback across entry points
- **WHEN** content generation is triggered from either Inspiration Dock or context menu
- **THEN** the loading feedback SHALL be visually consistent
- **AND** both entry points SHALL show the same loading state pattern

## ADDED Requirements

### Requirement: Output Card Dragging
The generated output cards (summary, mindmap) displayed on the canvas SHALL be draggable to allow users to reposition them.

#### Scenario: Drag output card to new position
- **WHEN** the user clicks and drags the drag handle of an output card
- **THEN** the card SHALL follow the mouse cursor during drag
- **AND** the card position SHALL update to the final drop position
- **AND** the new position SHALL be persisted in the generation task state

#### Scenario: Drag respects viewport transforms
- **WHEN** the user drags an output card while the canvas is zoomed or panned
- **THEN** the drag movement SHALL correctly account for the current viewport scale and offset
- **AND** the card SHALL visually follow the cursor accurately

#### Scenario: Drag visual feedback
- **WHEN** the user starts dragging an output card
- **THEN** the card SHALL display visual feedback indicating it is being dragged (e.g., elevated shadow, cursor change)
- **AND** the card z-index SHALL be elevated above other elements during drag

