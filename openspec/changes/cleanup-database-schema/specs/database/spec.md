## REMOVED Requirements

### Requirement: Knowledge Graph Tables
The system removes the `entities` and `relations` tables that were previously used for knowledge graph functionality.

#### Scenario: Table removal
- **WHEN** the migration is applied
- **THEN** the `entities` table SHALL be dropped
- **AND** the `relations` table SHALL be dropped
- **AND** associated indexes and foreign key constraints SHALL be removed

**Reason**: Knowledge graph feature was explored but not productized. These tables have no active usage.
**Migration**: N/A - data will be permanently deleted.

---

### Requirement: Deprecated Document Chunks Table
The system removes the deprecated `document_chunks` table.

#### Scenario: Table removal
- **WHEN** the migration is applied
- **THEN** the `document_chunks` table SHALL be dropped
- **AND** existing chunk data SHALL be permanently deleted

**Reason**: `document_chunks` has been replaced by `resource_chunks` which supports multiple resource types (documents, videos, articles) with a unified schema.
**Migration**: Existing data should be migrated to `resource_chunks` before running this migration if preservation is needed.
