## MODIFIED Requirements

### Requirement: Mindmap Generation
The Mindmap Agent SHALL generate hierarchical mindmaps with reasonable defaults and delegate layout to frontend.

#### Scenario: Generate mindmap with controlled node count
- **WHEN** the system generates a mindmap with default parameters
- **THEN** max_depth defaults to 2 (root + 2 levels)
- **AND** max_branches defaults to 4 per node
- **AND** total node count is limited to approximately 21 nodes (1 + 4 + 16)

#### Scenario: Emit nodes without hardcoded positions
- **WHEN** a node is generated and emitted via NODE_ADDED event
- **THEN** the node has `x=0` and `y=0` as placeholder coordinates
- **AND** the frontend applies layout algorithm to calculate actual positions
- **AND** node relationships (parentId, depth) are preserved for layout calculation

#### Scenario: Frontend applies layout on data receive
- **WHEN** the frontend receives mindmap data (streaming or loaded)
- **THEN** the layout algorithm (balanced/radial/tree) is applied
- **AND** all nodes receive non-overlapping positions
- **AND** the layout respects node hierarchy and depth

