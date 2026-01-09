# Design: Video Mindmap Navigation

## 1. Transcript Format Strategy

To enable the LLM to extract timestamps without confusing it or inflating the token count excessively, we will standardize the transcript format injected into the `{content}` variable.

### Format Specification
The `YouTubeExtractor` (and other video extractors) will be updated to output "Interval-based Transcripts". Instead of a timestamp for every subtitle line, we will group text into 30-60 second chunks or natural sentence boundaries prefixed with a timestamp.

**Example Content Injection:**
```text
[00:15] The core concept of a visual thinking assistant is not just about organizing nodes, but about spatial relationships.
[00:42] When we look at existing tools, they often treat data as flat lists. Our approach changes this by introducing a z-axis of depth.
[01:15] Let's dive into the technical implementation of the graph database backing this system.
```

## 2. Prompt Engineering

We will modify `app/backend/src/research_agent/application/graphs/mindmap_graph.py` to explicitly handle these timestamps.

### Modified `ROOT_PROMPT`

```python
ROOT_PROMPT = """Analyze the following document and identify the main topic/theme that should be the root of a mindmap.

Document Title: {title}

Document Content:
{content}

Respond with a JSON object containing:
{{
  "label": "Main topic label (brief, 3-5 words max)",
  "content": "A one-sentence summary of the main topic",
  "source_quote": "The EXACT quote from the document that best represents this main topic (copy verbatim, max 200 chars)",
  "source_location": "Page number, Section name, or Timestamp in seconds (e.g. '125' for [02:05]) if identifiable"
}}

Remember: Respond with ONLY the JSON object, nothing else."""
```

### Modified `BRANCHES_PROMPT`

```python
BRANCHES_PROMPT = """Based on the document content and the current mindmap structure, generate the next level of branches.

Document Content:
{content}

Current Node: {current_node_label}
Current Node Content: {current_node_content}
Depth Level: {depth} (0=root, higher=more specific)

Generate {max_branches} key sub-topics or aspects that branch from "{current_node_label}".
Each branch should be distinct and cover different aspects.

IMPORTANT RULES:
1. For each branch, include the EXACT quote from the source document that supports this sub-topic.
2. Check for timestamps in the content (format [MM:SS] or [HH:MM:SS]).
3. If a timestamp is present near the source quote, convert it to TOTAL SECONDS for the 'source_location' field (e.g., "[02:05]" -> "125").

Respond with a JSON object containing:
{{
  "branches": [
    {{
      "label": "Branch label (brief, 3-5 words max)",
      "content": "A brief explanation of this sub-topic",
      "source_quote": "The EXACT quote from the document supporting this branch (copy verbatim, max 200 chars)",
      "source_location": "Timestamp in seconds (e.g. '125'), Page number, or Section name"
    }}
  ]
}}

Remember: Respond with ONLY the JSON object, nothing else."""
```

### Modified `EXPLAIN_NODE_PROMPT` (in `mindmap_agent.py`)

This prompt is used when a user asks to "Explain" a specific node. We should also ensure it attributes the explanation to a specific time if possible.

```python
EXPLAIN_NODE_PROMPT = """Explain the following concept in the context of the document.

Document Content:
{content}

Node to Explain: {node_label}
Node Description: {node_content}

Provide a clear, detailed explanation of this concept. Include:
1. What it means in the context of the document
2. Why it's important
3. How it relates to the overall topic

If the content contains timestamps (e.g. [MM:SS]), reference the specific time where this is discussed.

Keep your explanation concise but informative (2-3 paragraphs)."""
```

## 3. Data Flow

1.  **Extraction**: `YouTubeExtractor` fetches transcript -> formats with `[MM:SS]` prefixes.
2.  **Generation**: `MindmapGraph` receives formatted content -> LLM extracts `label`, `quote`, and `source_location` ("125").
3.  **Storage**: Backend stores `source_location`="125" in `MindmapNode`.
4.  **Presentation**: Frontend `SourceContextPanel` reads "125" -> converts to "02:05" for display -> passes `125` to `react-player` for seeking.
