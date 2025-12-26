## MODIFIED Requirements

### Requirement: Mind Map Visualization
The system SHALL render mind map nodes as interactive, rich-content cards that reflect their generation state.

#### Scenario: Root Node "Processing" State
- **WHEN** the root node is being analyzed or generated
- **THEN** it renders as a prominent central card with AI brain icon
- **AND** displays a "PROCESSING CONTEXT" status with animated dots
- **AND** has a blue border glow to indicate active processing

#### Scenario: Generating Node "Skeleton" State
- **WHEN** a child node is currently being generated (streaming)
- **THEN** it renders with a dashed blue border
- **AND** displays skeleton loading bars for title and content
- **AND** has reduced opacity to indicate pending state

#### Scenario: Completed Node "Rich Card" State
- **WHEN** a node is fully generated
- **THEN** it renders as a clean white card with subtle shadow
- **AND** displays the node Label (Title) in bold
- **AND** displays the Content (Description) in secondary gray text
- **AND** shows a green checkmark icon in the top-right corner

#### Scenario: Pending Node "Ghost" State
- **WHEN** a node is queued but not yet processing
- **THEN** it renders with a gray dashed border
- **AND** displays a loading indicator (three dots)
- **AND** has low opacity (0.5) to indicate waiting state

#### Scenario: Node with Tags/Chips
- **WHEN** a completed node contains categorical data (e.g., competitors, keywords)
- **THEN** it displays content as colored pill-shaped tags
- **AND** tags have light background matching node accent color

#### Scenario: Curved Edge Connections
- **WHEN** nodes are connected by edges
- **THEN** edges render as smooth Bezier curves (not straight lines)
- **AND** a small dot appears at each connection anchor point
- **AND** edge color matches the source node state (blue for active, gray for pending)

#### Scenario: AI Insight Decoration
- **WHEN** the AI identifies a specific insight cluster
- **THEN** a floating dark badge appears above the relevant node
- **AND** it displays a sparkle icon and brief summary text
- **AND** a small diamond connector points to the node

