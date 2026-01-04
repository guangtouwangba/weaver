# Specification Delta: Canvas Node Synthesis

## ADDED Requirements

### Requirement: Drag-to-Merge Interaction
The system MUST allow users to initiate a merge operation by dragging any canvas item (Node, Note, Snippet) near another.

#### Scenario: Visual Cue
Given a user is dragging a Canvas Item A
When the user hovers Item A over Item B (or within close proximity)
Then a "Merge with AI insights?" visual prompt (e.g., a pill or button) overlaps the potential connection area
And the standard overlap prevention (pushing nodes away) is temporarily suppressed or secondary to the merge action.

#### Scenario: Triggering Synthesis
Given the "Merge with AI insights?" prompt is visible
When the user drops Node A onto the prompt or target zone
Then the system initiates the synthesis process
And a "Processing" node indicator is displayed in the target location.

### Requirement: Synthesis Output Structure
The system MUST generate a consolidated node with structured AI insights.

#### Scenario: Content Structure
Given two or more source nodes are merged
When the synthesis is complete
Then the new node displays a "Consolidated Insight" title
And the content includes succinct "Recommendation" and "Key Risk" sections
And the node metadata references the original source IDs.
