## ADDED Requirements
### Requirement: Project Chat Interface
The system SHALL provide a chat interface accessible from the canvas to allow users to interact with project content.

#### Scenario: Wake up chat
- **WHEN** the user clicks the "Ask AI" button at the bottom of the canvas
- **THEN** the chat panel SHALL slide up or appear overlaid on the canvas
- **AND** the latest chat history SHALL be displayed

#### Scenario: Chat Layout
- **WHEN** the chat panel is open
- **THEN** it SHALL display a list of previous messages
- **AND** it SHALL provide an input area at the bottom
- **AND** the input area SHALL support text entry and drag-and-drop targets

#### Scenario: Citation Click Interaction
- **WHEN** the user clicks on a citation chip/link in a chat answer
- **THEN** the Source Panel SHALL open (if closed)
- **AND** the system SHALL switch to the cited Document ID
- **AND** the system SHALL navigate to the specific Page Number
- **AND** the system SHALL highlight the cited text (Quote) in the document viewer

