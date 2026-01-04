# Design: Synthesize Canvas Nodes

## Interaction Design
To resolve the conflict between **Overlap Prevention** (pushing nodes away) and **Merge** (combining nodes), we will introduce a specific **Merge Drop Zone**.

1.  **Detection**: When *any* dragged item's (Node, Note, Snippet) bounding box overlaps significantly (e.g., >50%) with a target item *or* stays within proximity for >500ms:
    *   Show a visual "Merge Connection" (e.g., a purple pill/button between them).
2.  **Action**: If the user drops the item *while the Merge Connection is active*:
    *   Cancel standard Layout Overlap Resolution.
    *   **Show Choice Menu**: Display a radial or list menu at the drop location:
        *   🧩 **Connect**: "Find commonalities"
        *   💡 **Inspire**: "Reframe A with B"
        *   ⚔️ **Debate**: "Identify conflicts"
    *   User selects a mode -> Trigger synthesis with `mode` parameter.
3.  **Feedback**:
    *   Show "Processing AI..." loader in place of the potential new node.
    *   The new node is placed intelligently (e.g., centroid of sources).

## Backend Architecture
### 1. New Agent
`SynthesisAgent.synthesize(input_contents: List[str], mode: str) -> AsyncIterator[OutputEvent]`
*   **Role**: Specialized agent for combining multiple information sources.
*   **Prompts by Mode**:
    *   **Connect**: "Analyze these inputs. Identify common themes, structural similarities, and hidden links. Output: Shared Themes, Latent Connections."
    *   **Inspire**: "Use the concepts in Input A as a lens to re-examine Input B. How does A changing the meaning or potential of B? Output: New Perspective, Creative Leap."
    *   **Debate**: "Treat these inputs as opposing or complementary arguments. Where do they conflict? Which is more robust? Output: Key Tensions, Critical Analysis."

### 2. Service Layer
`OutputGenerationService.start_synthesize_nodes(..., node_ids: List[str])`
*   Retrieves content of specified nodes (resolving different node types).
*   Calls `SynthesisAgent`.
*   Streams events.

### 3. API
`POST /api/v1/outputs/{output_id}/synthesize`
*   Body: `{ node_ids: ["id1", "id2"], mode: "connect" | "inspire" | "debate" }`
*   Returns: `{ task_id: "..." }`

## Data Model
The new node will be a standard `MindmapNode` but with a specific **content structure** (Markdown) that the frontend recognizes to render the "Rich Card" view (Insight/Recommendation/Risk).

*   **Metadata**: Store `source_node_ids` in the node's `metadata` field to render "Synthesized from X sources".
