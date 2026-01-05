# Spec: Connection Styling

## ADDED Requirements

### Requirement: Visual Customization
The system SHALL support customization of edge visual properties including stroke width, color, line style, and markers.

#### Scenario: User customizes line style
- **Given** an existing connection
- **When** the user sets stroke width to 3px, color to red, and style to dashed
- **Then** the line should render with those properties.

### Requirement: Markers
The system SHALL support multiple types of start and end markers (Arrow, Circle, Diamond, None).

#### Scenario: User changes arrowhead
- **Given** a connection
- **When** the user selects "Diamond" for the start marker
- **Then** the start of the line should display a diamond shape.
