## ADDED Requirements
### Requirement: Drag to Chat Context
The system SHALL allow users to drag content from the canvas or source list into the chat to use as context for the next query.

#### Scenario: Drag Source Document
- **WHEN** the user drags a Source Document from the source list
- **AND** drops it into the Chat Input area
- **THEN** the document ID SHALL be added to the pending context list
- **AND** a visual indicator of the attached document SHALL appear in the input area

#### Scenario: Drag Canvas Node
- **WHEN** the user drags a generic Canvas Node (Note, Text, etc.)
- **AND** drops it into the Chat Input area
- **THEN** the text content of the node SHALL be added to the context

### Requirement: Drag Response to Canvas
The system SHALL allow users to drag AI responses from the chat onto the canvas to create new nodes.

#### Scenario: Drag Response
- **WHEN** the user drags an AI response message bubble
- **AND** drops it onto the Canvas
- **THEN** a new Note Node SHALL be created at the drop position
- **AND** the content of the node SHALL be the text of the AI response
