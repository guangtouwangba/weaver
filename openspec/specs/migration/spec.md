# migration Specification

## Purpose
TBD - created by archiving change fix-user-data-isolation. Update Purpose after archive.
## Requirements
### Requirement: Create Migration

The system SHALL include a database migration to add `user_id` column to all core resource tables.

#### Scenario: Verify Migration
- **WHEN** the migration is applied
- **THEN** the `user_id` column SHALL exist in the database tables

