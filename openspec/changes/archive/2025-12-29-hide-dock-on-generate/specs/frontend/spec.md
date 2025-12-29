# Frontend Capability Spec

## MODIFIED Requirements

### Requirement: Inspiration Dock visibility

The Inspiration Dock on the freeform canvas MUST only be visible when the canvas is empty AND no generation action is in progress.

#### Scenario: Dock hides when SmartStart is triggered

**Given** the freeform canvas is empty  
**And** available files exist in the sidebar  
**And** the Inspiration Dock is visible  
**When** the user clicks the "Summary" button on the dock  
**Then** the Inspiration Dock should immediately hide  
**And** only the generation loading indicator should be visible

#### Scenario: Dock reappears if generation fails and canvas remains empty

**Given** a SmartStart generation action has been triggered  
**And** the canvas is still empty  
**When** the generation fails or is cancelled  
**Then** the Inspiration Dock should reappear
