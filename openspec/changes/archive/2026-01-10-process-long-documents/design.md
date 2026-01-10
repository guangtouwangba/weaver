# Design: Recursive Map-Reduce & Semantic Fusion

## 1. Tree-oriented Map-Reduce (ToM)

We will implement a `RecursiveMindmapGenerator` that operates in phases.

### Phase 1: Chunking & Mapping
- **Input**: Full document text OR Video Transcript.
- **Chunking Strategy**:
    - **Documents**: Split by Page Groups or Semantic Sections (approx 4k tokens).
    - **Videos**: Split by Time Intervals (e.g., 10-minute segments) to preserve temporal context.
- **Map**: For each chunk `C_i`, run `MindmapAgent.generate_subgraph(C_i)` in parallel.
- **Output**: List of `N` disconnected `MindmapGraph` objects.

### Phase 2: Recursive Reduction
- **Input**: List of `MindmapGraph` objects.
- **Process**:
    1. Group adjacent graphs: `(G1, G2), (G3, G4)...`
    2. For each pair `(Ga, Gb)`:
       - **Synthesize**: Create a "Bridge Node" that represents the common theme of both sections.
       - **Fuse**: Run `SemanticFusion(Ga, Gb)` to merge identical nodes.
    3. Repeat until 1 graph remains.

## 2. Semantic Fusion Algorithm

To solve the "AI" vs "Artificial Intelligence" problem:

1.  **Embed**: Calculate vector embeddings for all node labels in `Ga` and `Gb`.
2.  **Compare**: Compute cosine similarity matrix.
3.  **Cluster**: Identify pairs/groups with similarity > `0.85` (configurable).
4.  **Unify (LLM)**:
    - Prompt: *"Merge these concepts: ['AI', 'Artificial Intelligence']. Choose the most precise label and combine their descriptions."*
5.  **Source Aggregation (Critical for Video)**:
    - If Node A has `SourceRef(time=100s)` and Node B has `SourceRef(time=500s)`, the Merged Node M must have `[SourceRef(time=100s), SourceRef(time=500s)]`.
    - **Frontend Implication**: Clicking Node M should ideally show a list of timestamps or default to the *first* occurrence.

## 3. Data Structures

```python
class SubGraph:
    nodes: List[MindmapNode]
    edges: List[MindmapEdge]
    embeddings: Dict[str, List[float]]  # Cache node embeddings

class MergeCandidate:
    node_ids: List[str]
    similarity_score: float
    suggested_label: Optional[str]
```

## 4. Prompts

**`MERGE_CONCEPTS_PROMPT`**
```text
The following concepts appear to be similar:
1. "AI" (Description: ...)
2. "Artificial Intelligence" (Description: ...)

Are these referring to the same core concept in this context?
If YES, provide a single unified label and a combined description.
If NO, explain why they should remain separate.
```
