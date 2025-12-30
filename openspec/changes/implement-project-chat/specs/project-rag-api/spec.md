## ADDED Requirements
### Requirement: Project RAG Endpoint
The system SHALL provide an API endpoint to answer user queries based on project documents and provided context.

#### Scenario: Answer with Context
- **WHEN** the frontend sends a query with a Project ID
- **AND** optionally provides specific context item IDs (documents)
- **THEN** the system SHALL retrieve relevant chunks from the specified documents (or all project documents if none specified)
- **AND** generate an answer using the LLM
- **AND** return the answer text along with citations

### Requirement: Source Attribution
The system SHALL provide citations for every answer generated from project documents.

#### Scenario: Citation Format
- **WHEN** the system generates an answer
- **THEN** it SHALL return a list of source references (Document ID, Page Number, Quote) used for the answer
- **AND** the Quote SHALL contain the exact text content used from the source to allow for precise highlighting
- **AND** the frontend SHALL display these citations interactively (e.g., clickable to open source)
