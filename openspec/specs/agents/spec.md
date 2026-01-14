# agents Specification

## Purpose
TBD - created by archiving change add-document-summary. Update Purpose after archive.
## Requirements
### Requirement: Document Summary Agent
The system SHALL provide an agent capable of synthesizing multiple documents into a cohesive summary.

#### Scenario: Multi-document summarization
- **WHEN** the agent receives a list of document IDs
- **THEN** it analyzes the content of these documents
- **AND** returns a structured response containing:
  - A high-level narrative summary
  - Key findings or metrics
  - Relevant category tags (e.g., Strategy, Insights)

### Requirement: RAG Agent
The system SHALL provide a RAG (Retrieval-Augmented Generation) Agent that orchestrates document retrieval, memory access, and answer generation through a tool-based architecture.

#### Scenario: Simple question answering
- **WHEN** a user asks a factual question about uploaded documents
- **THEN** the Agent retrieves relevant document chunks
- **AND** generates an answer with proper citations
- **AND** streams the response token by token

#### Scenario: Complex question with memory
- **WHEN** a user asks a follow-up question referencing previous conversation
- **THEN** the Agent retrieves session summary and relevant past discussions
- **AND** combines memory context with document retrieval
- **AND** provides a coherent answer that builds on previous context

#### Scenario: Intent-based tool selection
- **WHEN** a user asks a comparison question
- **THEN** the Agent classifies the intent as "comparison"
- **AND** selects appropriate retrieval and generation strategies
- **AND** structures the response as a comparison format

### Requirement: Global XML Context Format
The system SHALL use XML-structured context (Mega-Prompt) for all generation tasks to ensure citation accuracy and prevent hallucinations.

#### Scenario: XML Context Injection
- **WHEN** the Agent calls the LLM for generation
- **THEN** the context is formatted with `<documents>` and `<document>` XML tags
- **AND** strict citation rules are injected via `<output_rules>`

#### Scenario: Verified Citation Generation
- **WHEN** the Agent generates an answer
- **THEN** it MUST use `<cite doc_id="..." quote="...">` format
- **AND** the `quote` attribute MUST be a verbatim extract from the source document

### Requirement: RAG Agent Tools
The system SHALL provide a set of reusable tools for the RAG Agent to perform its tasks.

#### Scenario: Vector retrieval tool
- **WHEN** the Agent invokes the vector_retrieve tool with a query
- **THEN** the tool returns relevant document chunks from the vector store
- **AND** respects project_id and document_id filtering if specified

#### Scenario: Document reranking tool
- **WHEN** the Agent invokes the rerank tool with retrieved documents
- **THEN** the tool uses LLM-based scoring to reorder documents by relevance
- **AND** returns the top-k most relevant documents

#### Scenario: Document grading tool
- **WHEN** the Agent invokes the grade tool with documents and query
- **THEN** the tool evaluates binary relevance of each document
- **AND** filters out irrelevant documents

#### Scenario: Query rewriting tool
- **WHEN** the Agent invokes the query_rewrite tool with a question and chat history
- **THEN** the tool rewrites the query to resolve pronoun references
- **AND** returns an expanded query for better retrieval

### Requirement: RAG Agent Memory
The system SHALL provide a memory module that enables the RAG Agent to maintain context across conversations.

#### Scenario: Session summary retrieval
- **WHEN** the Agent needs context from earlier in a long conversation
- **THEN** the memory module provides a summarized version of older messages
- **AND** reduces token usage while preserving key information

#### Scenario: Episodic memory retrieval
- **WHEN** the Agent needs to recall past similar discussions
- **THEN** the memory module performs semantic search over stored Q&A pairs
- **AND** returns relevant past interactions with similarity scores

#### Scenario: Memory storage
- **WHEN** a conversation turn completes successfully
- **THEN** the memory module stores the Q&A pair asynchronously
- **AND** enables future retrieval of this interaction

### Requirement: RAG Agent Streaming
The system SHALL preserve streaming capabilities when using the RAG Agent architecture.

#### Scenario: Token-by-token streaming
- **WHEN** the Agent generates an answer
- **THEN** tokens are streamed via SSE as they are produced
- **AND** video timestamps are transformed to clickable links
- **AND** citations are parsed and emitted separately

#### Scenario: Status event streaming
- **WHEN** the Agent invokes a tool
- **THEN** a status event is emitted indicating the current step
- **AND** the frontend can display progress to the user

