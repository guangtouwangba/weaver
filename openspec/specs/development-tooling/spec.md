# development-tooling Specification

## Purpose
TBD - created by archiving change add-fps-monitor. Update Purpose after archive.
## Requirements
### Requirement: FPS Monitor in Development Mode
The frontend SHALL display a floating FPS monitor widget when running in development mode to help developers identify performance issues.

#### Scenario: FPS widget visible in development
- **Given** the application is running in development mode (`NODE_ENV=development`)
- **When** a user loads any page
- **Then** a stats.js FPS monitor widget is visible in the top-left corner

#### Scenario: FPS widget hidden in production
- **Given** the application is built for production
- **When** a user loads any page
- **Then** no FPS monitor widget is visible

