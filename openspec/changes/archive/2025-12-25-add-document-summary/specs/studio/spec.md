## ADDED Requirements

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

