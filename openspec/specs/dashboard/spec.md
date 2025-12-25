# dashboard Specification

## Purpose
TBD - created by archiving change redesign-dashboard-layout. Update Purpose after archive.
## Requirements
### Requirement: Dashboard Layout Structure
The dashboard SHALL be organized into distinct sections to prioritize recent work and quick actions.

#### Scenario: Dashboard sections
- **WHEN** a user visits the dashboard
- **THEN** they see the "Welcome" header, "Recent Projects" section, "Start from a template" section, and "Project List" section in vertical order.

### Requirement: Recent Projects Section
The dashboard SHALL display the most recently modified projects for quick access.

#### Scenario: Display recent projects
- **WHEN** the user has existing projects
- **THEN** the top 4 most recently updated projects are displayed as visual cards in the "Recent Projects" section.

### Requirement: Project Templates
The dashboard SHALL provide predefined templates to start new projects.

#### Scenario: Template selection
- **WHEN** the user views the "Start from a template" section
- **THEN** they see options for "Market Analysis", "Brainstorming", "Roadmap", and "Retrospective" templates.

### Requirement: Project Filtering
The dashboard SHALL allow filtering the full list of projects.

#### Scenario: Filter tabs
- **WHEN** the user views the "Recent Projects" or "All Projects" list
- **THEN** they can switch between "All Projects", "Starred", and "Shared with me" tabs (UI only for MVP).

