# Specification: Dashboard UI

## Summary
Refines the Dashboard UI to resolve navigation conflicts and improve card information density.

## MODIFIED Requirements

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
 
## ADDED Requirements
 
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
