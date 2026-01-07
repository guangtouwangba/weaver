# studio Specification Changes

## ADDED Requirements

### Requirement: Magic Cursor Tool
The Magic Cursor SHALL serve as a dedicated mode for AI intent on the whiteboard.

#### Scenario: Activation
- **WHEN** the user selects the "Magic Cursor" tool from the toolbar (Sparkle icon)
- **THEN** the cursor changes to a "magic" state (sparkles/colors)
- **AND** the selection mode changes to `MagicSelection`

### Requirement: Magic Selection
The system SHALL provide a specialized selection interaction for the Magic Cursor.

#### Scenario: Selection Visuals
- **WHEN** the user drags to select an area with the Magic Cursor
- **THEN** the selection box displays a flowing gradient border ("Magic selection")
- **AND** the fill is a subtle iridescent wash

#### Scenario: Intent Menu
- **WHEN** the user releases the mouse after a magic selection
- **THEN** an "Intent Menu" automatically floats at the bottom-right of the selection
- **AND** options include "Draft Article" and "Action List"

### Requirement: Super Cards
The system SHALL generate specialized "Super Cards" as result containers.

#### Scenario: Document Card Generation
- **WHEN** the user selects "Draft Article"
- **THEN** a Document Card is generated
- **AND** it features A4-like styling, header/footer, and export options
- **AND** it retains a "Snapshot Context" of the original selection area for refreshing

#### Scenario: Ticket Card Generation
- **WHEN** the user selects "Action List"
- **THEN** a Ticket Card is generated
- **AND** it features a receipt-like style with torn edges
- **AND** it contains interactive checkboxes

