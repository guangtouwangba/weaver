# settings Specification

## Purpose
TBD - created by archiving change add-custom-model-support. Update Purpose after archive.
## Requirements
### Requirement: Custom Model Management

Users SHALL be able to add, edit, and delete custom LLM models that persist to the database and appear alongside built-in model options.

#### Scenario: User adds a custom model
- **WHEN** user clicks "Add Custom Model" on the settings page
- **THEN** a modal SHALL appear for entering model details (ID, label, description)
- **AND** the model SHALL be saved to the database upon confirmation

#### Scenario: Custom models appear in selection list
- **WHEN** user views the model selection on settings page
- **THEN** custom models SHALL appear alongside built-in models
- **AND** custom models SHALL be visually distinguished (e.g., badge or icon)

#### Scenario: User edits a custom model
- **WHEN** user clicks edit on a custom model
- **THEN** a modal SHALL appear with pre-filled model details
- **AND** changes SHALL be saved to the database upon confirmation

#### Scenario: User deletes a custom model
- **WHEN** user clicks delete on a custom model
- **THEN** a confirmation dialog SHALL appear
- **AND** the model SHALL be removed from the database upon confirmation
- **AND** if the deleted model was selected, selection SHALL revert to default

### Requirement: Model List Layout

The model selection interface SHALL display models in a vertical list format instead of a grid layout.

#### Scenario: Model list displays vertically
- **WHEN** user views model selection on settings page
- **THEN** models SHALL be displayed as a vertical scrollable list
- **AND** each list item SHALL show model name, description, and action buttons (for custom models)

### Requirement: Custom Model Data Persistence

Custom models SHALL be stored in the database with user isolation.

#### Scenario: Custom models are user-scoped
- **WHEN** a user creates a custom model
- **THEN** the model SHALL only be visible to that user
- **AND** other users SHALL NOT see the model

#### Scenario: Custom models persist across sessions
- **WHEN** user logs out and logs back in
- **THEN** previously created custom models SHALL still be available

