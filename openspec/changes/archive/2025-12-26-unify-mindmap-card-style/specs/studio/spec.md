## MODIFIED Requirements

### Requirement: Mind Map Card Display
The system SHALL display the generated mind map in a unified card format with consistent styling across all generation states, and provide full editing capabilities in expanded view.

#### Scenario: Mind Map presentation during generation
- **WHEN** the mind map generation starts
- **THEN** a Mind Map Card appears in the workspace
- **AND** the card displays:
  - A header with an icon badge (green gradient), drag handle, and title
  - A "MINDMAP" chip tag
  - A streaming indicator (spinner) next to the title
  - A preview area showing nodes as they appear incrementally
- **AND** nodes appear incrementally ("grow") as they are generated
- **AND** the card shows a simplified or zoomed-out view of the structure

#### Scenario: Mind Map presentation after completion
- **WHEN** the mind map generation completes
- **THEN** the Mind Map Card retains the same visual styling as during generation
- **AND** the card displays:
  - The same header layout with icon badge, drag handle, and title
  - A "MINDMAP" chip tag
  - A "{count} NODES" chip tag showing total node count
  - The streaming indicator is hidden
- **AND** the user can click to expand to full view with editing

#### Scenario: Full Mind Map expansion with editing
- **WHEN** the user interacts with the Mind Map Card (e.g., clicks expand button)
- **THEN** the mind map opens in a full view modal with MindMapEditor
- **AND** the user can freely zoom using:
  - Mouse scroll wheel
  - Pinch gestures on trackpad
  - Zoom in/out buttons
- **AND** the user can pan the canvas by dragging the background
- **AND** the user can switch between layouts (radial, tree, balanced)
- **AND** the user can edit nodes (add, delete, edit label/content)
- **AND** the user can export the mindmap (PNG, JSON)

#### Scenario: Mind Map card visual consistency
- **WHEN** the Mind Map Card is shown via any display method (canvas overlay or dock overlay)
- **THEN** the card uses identical visual styling including:
  - Green gradient icon badge
  - Drag handle in header
  - "MINDMAP" chip tag
  - Node count chip when available
  - Same border, spacing, and dimensions
