# models Specification

## Purpose
TBD - created by archiving change fix-user-data-isolation. Update Purpose after archive.
## Requirements
### Requirement: Add User ID to Models

The system SHALL include `user_id` field in all ORM models for core resource tables.

#### Scenario: Verify Model has user_id
- **WHEN** an ORM model is inspected
- **THEN** it SHALL have a `user_id` column definition

