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
The dashboard MUST provide clear filtering via tabs under a unified "Projects" heading.

#### Scenario: Switching Tabs
Given the dashboard is open
When clicking "Recent"
Then only projects modified in the last 7 days are shown

#### Scenario: All Projects
Given the dashboard is open
When clicking "All Projects"
Then all unfiltered projects are shown

---

### Requirement: Card Visuals
Project cards MUST maximize relevant information and minimize visual noise.

#### Scenario: No Description
Given a project with no description
When the card is rendered
Then the description area is hidden (no "No description" text)

#### Scenario: Project Icon
Given a project named "Alpha"
When the card is rendered
Then a colored icon with "A" is displayed instead of a generic placeholder image

