# api Specification

## Purpose
TBD - created by archiving change fix-user-data-isolation. Update Purpose after archive.
## Requirements
### Requirement: Pass User ID in API

The system SHALL pass `user_id` in all API endpoints to ensure data isolation.

#### Scenario: Verify API passes user_id
- **WHEN** an API endpoint is called
- **THEN** the `user_id` SHALL be passed to the repository layer

---

