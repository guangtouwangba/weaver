# auth Specification Delta

## Purpose

Update to enforce user-scoped project access across all project-scoped API endpoints.

## MODIFIED Requirements

### Requirement: User-Scoped Project Access

The system SHALL verify project ownership on every project-scoped endpoint before granting access to resources.


#### Scenario: Access denied for chat on non-owned project
- **WHEN** a user sends a chat message to a project they do not own
- **THEN** the system returns HTTP 403 Forbidden
- **AND** no chat message is processed

#### Scenario: Access denied for output generation on non-owned project
- **WHEN** a user requests output generation on a project they do not own
- **THEN** the system returns HTTP 403 Forbidden
- **AND** no generation task is started

#### Scenario: Access denied for canvas data on non-owned project
- **WHEN** a user requests canvas data from a project they do not own
- **THEN** the system returns HTTP 403 Forbidden
- **AND** no canvas data is returned

#### Scenario: Access denied for URL extraction on non-owned project
- **WHEN** a user submits a URL for extraction to a project they do not own
- **THEN** the system returns HTTP 403 Forbidden
- **AND** no extraction task is created

#### Scenario: Access denied for document confirmation on non-owned project
- **WHEN** a user confirms a document upload to a project they do not own
- **THEN** the system returns HTTP 403 Forbidden
- **AND** no document record is created

