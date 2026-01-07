## ADDED Requirements
### Requirement: Mind Map Logic Linking
The system SHALL allow users to define logical relationships between nodes through interactive linking.

#### Scenario: Drag to link interaction
- **WHEN** a user hovers over a mind map node
- **THEN** connection handles appear (or a specific mode is activated)
- **WHEN** the user drags from a handle to another node
- **THEN** a temporary connection line follows the cursor
- **WHEN** the user releases the drag over a target node
- **THEN** a "Link Type" selection dialog appears

#### Scenario: Define Link Type
- **WHEN** the Link Type dialog is open
- **THEN** the user can select from:
  - "Structural" (Default, existing parent/child behavior)
  - "Support" (Evidence supports Conclusion)
  - "Contradict" (Evidence contradicts Conclusion)
  - "Relates To" (Neutral association)
- **WHEN** a type is selected and confirmed
- **THEN** the edge is created with the specified semantic type

#### Scenario: Visual Styling of Logic Links
- **WHEN** a "Support" link is rendered
- **THEN** it appears as a **Green** solid line with an arrow pointing to the target
- **WHEN** a "Contradict" link is rendered
- **THEN** it appears as a **Red** solid line (potentially with a cross mark or distinct style)
- **WHEN** a "Relates To" link is rendered
- **THEN** it appears as a **Neutral/Blue** dashed line

### Requirement: AI Relation Verification
The system SHALL provide AI capabilities to verify the logical validity of defined relationships.

#### Scenario: Trigger Verification
- **WHEN** a user selects two connected nodes (or the edge itself)
- **AND** the edge has a semantic type (Support/Contradict)
- **THEN** a "Verify Relation" action is available in the context menu
- **WHEN** the action is clicked
- **THEN** the system analyzes the content of both nodes using AI
- **AND** determines if the relationship holds true

#### Scenario: Verification Feedback - Valid
- **WHEN** the AI confirms the relationship is valid
- **THEN** a success toast or indicator appears
- **AND** the edge may receive a "Verified" badge or visual enhancer

#### Scenario: Verification Feedback - Invalid
- **WHEN** the AI finds the relationship weak or unsupported
- **THEN** the system provides constructive feedback (e.g., "The evidence A discusses X, but conclusion B is about Y. Connection is weak.")
- **AND** suggestions for strengthening the argument are offered
