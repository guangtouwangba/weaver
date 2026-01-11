# Spec: Confirmation UI

## ADDED Requirements

### Requirement: Confirm Dialog Component
The application SHALL provide a reusable confirmation dialog to prevent accidental destructive actions.

#### Scenario: Deleting a sensitive item
- **Given** a user clicks a delete button for a document or session.
- **When** the confirmation dialog opens.
- **Then** it must display a clear title (e.g., "Delete Document?").
- **And** it must display a message explaining the consequences.
- **And** it must provide "Cancel" and "Confirm" (or "Delete") buttons.

### Requirement: Visual Hierarchy for Destructive Actions
Confirmation dialogs for destructive actions MUST use distinct visual styles to warn the user.

#### Scenario: Delete button styling
- **Given** a confirmation dialog for deletion.
- **Then** the confirm button should use a "danger" or "error" theme (e.g., red background).

#### Scenario: Focus management
- **Given** the confirmation dialog is open.
- **Then** the "Cancel" button should be the default focused element (if applicable) or the "Confirm" button should be clearly distinguished but not easily mis-clicked.
