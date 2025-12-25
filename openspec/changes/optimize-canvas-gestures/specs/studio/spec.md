## ADDED Requirements

### Requirement: Canvas Navigation Gestures
The canvas MUST support standard trackpad and mouse gestures for navigation.

#### Scenario: Panning with Trackpad
- **WHEN** the user performs a two-finger scroll gesture (without pinching)
- **THEN** the canvas viewport should pan in the direction of the scroll
- **AND** the zoom level should remain unchanged

#### Scenario: Zooming with Trackpad
- **WHEN** the user performs a pinch gesture (two fingers moving apart or together)
- **THEN** the canvas viewport should zoom in or out centered on the pointer position
- **AND** the viewport position should adjust to keep the content under the pointer stable
