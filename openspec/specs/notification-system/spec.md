# notification-system Specification

## Purpose
The application SHALL provide a global notification system for displaying success and error messages that can be triggered from any component or hook.

## Requirements

### Requirement: Global Notification Provider
The application SHALL provide a global context to manage success and error notifications that can be triggered from any component or hook.

#### Scenario: Triggering a success notification
- **GIVEN** a user successfully completes an action (e.g., creating a project)
- **WHEN** the component calls `notifySuccess("Project created")`
- **THEN** a visual "Toast" appears with the message and a success theme (green)

#### Scenario: Triggering an error notification
- **GIVEN** an API call fails during a deletion
- **WHEN** the catch block calls `notifyError("Failed to delete")`
- **THEN** a visual "Toast" appears with the error message and an error theme (red)

### Requirement: Visual Alert Appearance
Notifications MUST be clearly visible but non-intrusive.

#### Scenario: Positioning and Styling
- **GIVEN** one or more active notifications
- **THEN** they should be stacked at the bottom-center of the viewport
- **AND** they should have a shadow, rounded corners, and include an icon representing the status (check for success, alert for error)

### Requirement: Auto-Dismiss and Manual Close
Notifications SHALL disappear automatically after a short delay but allow manual dismissal.

#### Scenario: Auto-dismiss
- **GIVEN** a notification is displayed
- **THEN** it should automatically disappear after 5 seconds

#### Scenario: Manual dismissal
- **GIVEN** a notification is displayed
- **WHEN** the user clicks the close (X) button
- **THEN** it should disappear immediately
