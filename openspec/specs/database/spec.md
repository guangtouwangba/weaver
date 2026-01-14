# database Specification

## Purpose
TBD - created by archiving change cleanup-database-schema. Update Purpose after archive.
## Requirements
### Requirement: Clean Database Schema
The system MUST maintain a clean database schema with only actively used tables.

#### Scenario: Initial schema migration
- **WHEN** a fresh database is initialized
- **THEN** the system MUST create all 22 required tables via a single initial migration

#### Scenario: Legacy tables removed
- **WHEN** the database schema is rebuilt
- **THEN** the system MUST NOT include deprecated tables (document_chunks, entities, relations)

### Requirement: Resource Chunks Table
The system MUST use `resource_chunks` table as the unified storage for all document chunks.

#### Scenario: Document chunk storage
- **WHEN** a document is processed
- **THEN** chunks MUST be stored in the `resource_chunks` table with vector embeddings

### Requirement: Database Reset Command
The system MUST provide a `make clean-migration` command to reset the local database.

#### Scenario: Clean migration execution
- **WHEN** developer runs `make clean-migration`
- **THEN** the system MUST drop all tables and recreate the schema from scratch

