# Spec: Notification System

## ADDED Requirements

### Requirement: Global Notification Provider
The application SHALL provide a global context to manage success and error notifications that can be triggered from any component or hook.

#### Scenario: Triggering a success notification
- **Given** a user successfully completes an action (e.g., creating a project).
- **When** the component calls `notifySuccess("Project created")`.
- **Then** a visual "Toast" appears with the message and a success theme (green).

#### Scenario: Triggering an error notification
- **Given** an API call fails during a deletion.
- **When** the catch block calls `notifyError("Failed to delete")`.
- **Then** a visual "Toast" appears with the error message and an error theme (red).

### Requirement: Visual Alert Appearance
Notifications MUST be clearly visible but non-intrusive.

#### Scenario: Positioning and Styling
- **Given** one or more active notifications.
- **Then** they should be stacked at the bottom-center of the viewport.
- **And** they should have a shadow, rounded corners, and include an icon representing the status (check for success, alert for error).

### Requirement: Auto-Dismiss and Manual Close
Notifications SHALL disappear automatically after a short delay but allow manual dismissal.

#### Scenario: Auto-dismiss
- **Given** a notification is displayed.
- **Then** it should automatically disappear after 5 seconds.

#### Scenario: Manual dismissal
- **Given** a notification is displayed.
- **When** the user clicks the close (X) button.
- **Then** it should disappear immediately.
