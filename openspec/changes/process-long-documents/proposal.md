# Process Long Documents & Videos with Map-Reduce & Semantic Fusion

## Summary
Implement advanced long-content processing capabilities using **Tree-oriented Map-Reduce (ToM)** and **Vector-based Semantic Fusion** to generate coherent mindmaps from sources exceeding the context window, including **long documents (100+ pages)** and **long videos (1+ hours)**.

## Background
Currently, the system attempts to process content by truncating or using simple chunking. This fails for:
1.  **Massive PDFs**: Books, academic papers.
2.  **Long Video Transcripts**: 2-3 hour lectures or podcasts where the transcript alone can exceed 30k tokens.

To handle these extensive materials, we need a unified strategy that preserves both global structure and local details, regardless of the source medium.

## Problem
1.  **Context Window Limits**: Direct LLM calls fail for large texts/transcripts.
2.  **Fragmented Insights**: Simple chunking leads to disconnected mindmap nodes.
3.  **Redundancy**: Merging chunks naively results in duplicate concepts.
4.  **Video Specifics**: Long videos need time-aware chunking, and merging nodes requires handling timestamp ranges.

## Solution
1.  **Tree-oriented Map-Reduce (ToM)**:
    -   **Map**: Parallelly generate sub-mindmaps for chunks (Text Segments or Time Intervals).
    -   **Reduce**: Recursively merge adjacent/related sub-mindmaps into higher-level structures.
2.  **Semantic Fusion**:
    -   Use vector embeddings to identify similar nodes across chunks.
    -   Merge nodes with high cosine similarity (>0.85).
    -   **Unified Source Refs**: When merging nodes from different video chunks, aggregate their timestamps (e.g., "discussed at [05:20] and [45:10]").

## Risks
-   **Latency**: Recursive processing is slower.
-   **Cost**: Higher token/embedding usage.
-   **Timestamp Complexity**: Merging nodes from different times in a video might make "jump to timestamp" logic ambiguous (which one to jump to?).
