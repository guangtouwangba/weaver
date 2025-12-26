## MODIFIED Requirements

### Requirement: Mindmap Generation
The Mindmap Agent SHALL generate hierarchical mindmaps from document content using a LangGraph-based workflow.

#### Scenario: Generate mindmap with LangGraph workflow
- **WHEN** the system receives a request to generate a mindmap
- **THEN** the agent executes a StateGraph workflow with nodes: analyze → generate_root → expand_level
- **AND** each graph node emits OutputEvents for real-time streaming
- **AND** the workflow continues expanding levels until max_depth is reached
- **AND** the final output is a collection of nodes and edges in JSON format

#### Scenario: Real-time node streaming
- **WHEN** the LangGraph workflow generates a new node
- **THEN** an OutputEvent of type NODE_ADDED is emitted immediately
- **AND** the frontend receives the event via WebSocket
- **AND** the node appears on the canvas before the full mindmap is complete

#### Scenario: Level-by-level expansion
- **WHEN** the workflow completes generating nodes at depth N
- **THEN** it emits a LEVEL_COMPLETE event
- **AND** proceeds to expand nodes at depth N+1
- **AND** continues until max_depth is reached or no more nodes to expand

#### Scenario: Error handling in workflow
- **WHEN** any graph node encounters an error
- **THEN** the error is captured in the state
- **AND** a GENERATION_ERROR event is emitted
- **AND** the workflow terminates gracefully

