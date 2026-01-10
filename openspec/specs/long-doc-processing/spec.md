# long-doc-processing Specification

## Purpose
TBD - created by archiving change process-long-documents. Update Purpose after archive.
## Requirements
### Requirement: Recursive Mindmap Generation (Map-Reduce)
The system SHALL support generating mindmaps from long documents AND video transcripts by recursively processing content chunks.

#### Scenario: Processing Large Documents
Given a document exceeding the LLM context window (e.g. > 20k tokens)
When the user requests a mindmap
Then the system should split the document into semantic chunks
And generate independent sub-mindmaps for each chunk (Map Phase)
And recursively merge these sub-mindmaps into a single coherent graph (Reduce Phase)

#### Scenario: Processing Long Video Transcripts
Given a video transcript exceeding the context window (e.g. > 1 hour)
When the user requests a mindmap
Then the system should split the transcript into time-based chunks (e.g. 10-minute segments)
And generate sub-mindmaps for each segment
And recursively merge them while preserving timestamp references in the final nodes

### Requirement: Semantic Node Fusion with Source Aggregation
The system SHALL deduplicate semantically identical nodes and aggregate their source references (page numbers or timestamps).

#### Scenario: Merging Redundant Nodes
Given two sub-mindmaps containing similar concepts (e.g. "AI" and "Artificial Intelligence")
When the system merges these sub-maps
Then it should calculate the cosine similarity of node embeddings
And if similarity > 0.85, it should invoke the LLM to unify them into a single node
And edges from both original nodes should be reconnected to the unified node

#### Scenario: Aggregating Video Timestamps
Given two nodes representing the same concept from different times in a video (e.g. "05:00" and "45:00")
When they are merged into a single node
Then the new node should contain `SourceRef`s for BOTH timestamps
So that the user can see all occurrences of the concept in the video

