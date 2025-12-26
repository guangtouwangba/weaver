## ADDED Requirements

### Requirement: Output Persistence Across Sessions
The system SHALL restore previously generated outputs (summary, mindmap) when a user returns to a project.

#### Scenario: Load most recent summary on page mount
- **WHEN** a user opens a project page
- **AND** a completed summary output exists for that project
- **THEN** the most recent complete summary is loaded into state
- **AND** the summary data is available for viewing in the Inspiration Dock
- **AND** the summary overlay is NOT automatically shown

#### Scenario: Load most recent mindmap on page mount
- **WHEN** a user opens a project page
- **AND** a completed mindmap output exists for that project
- **THEN** the most recent complete mindmap is loaded into state
- **AND** the mindmap data is available for viewing in the Inspiration Dock
- **AND** the mindmap overlay is NOT automatically shown

#### Scenario: No outputs exist
- **WHEN** a user opens a project page
- **AND** no completed outputs exist for that project
- **THEN** the summary and mindmap states remain null
- **AND** the Inspiration Dock shows generation options normally

#### Scenario: Multiple outputs exist
- **WHEN** a user opens a project page
- **AND** multiple completed outputs of the same type exist
- **THEN** only the most recently created output is loaded
- **AND** older outputs remain in the database for potential future history features

