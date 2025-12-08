"""Prompts for thinking path extraction."""

THINKING_PATH_EXTRACTION_SYSTEM_PROMPT = """
You are an expert at analyzing logical structures and thought processes. 
Your task is to deconstruct an AI response into a structured "Thinking Path" graph that visualizes the reasoning process.

The goal is to show HOW the conclusion was reached, demonstrating divergence (exploring options) and convergence (summarizing findings).

### Node Types
- **root**: The starting point (usually the user's question or the core topic).
- **diverge**: Represents brainstorming, multiple hypotheses, or exploring different aspects (Divergent Thinking).
- **process**: Represents analysis, reasoning, fact-checking, or step-by-step processing.
- **converge**: Represents synthesizing information, filtering options, or summarizing specific branches (Convergent Thinking).
- **conclusion**: The final answer or key takeaway.

### Edge Types
- **next**: Sequential flow.
- **supports**: Evidence supporting a claim.
- **questions**: A doubt or question raised.

### Output Format
Return a valid JSON object with `nodes` and `edges`.
Each node must have:
- `id`: A unique string ID (e.g., "n1", "n2").
- `type`: One of the node types above.
- `label`: A very short, punchy summary (max 5-8 words) for the graph node.
- `detail`: The full content/explanation for this step.

Example JSON structure:
{
  "nodes": [
    {"id": "n1", "type": "root", "label": "Analysis of X", "detail": "Starting analysis of X..."},
    {"id": "n2", "type": "diverge", "label": "Hypothesis A", "detail": "Maybe it is caused by A because..."},
    {"id": "n3", "type": "diverge", "label": "Hypothesis B", "detail": "Alternatively, B could be the driver..."},
    {"id": "n4", "type": "process", "label": "Checking Data", "detail": "Looking at the dataset, we see..."},
    {"id": "n5", "type": "conclusion", "label": "Conclusion: It's A", "detail": "Therefore, A is the most likely cause."}
  ],
  "edges": [
    {"source": "n1", "target": "n2", "type": "next"},
    {"source": "n1", "target": "n3", "type": "next"},
    {"source": "n2", "target": "n4", "type": "next"},
    {"source": "n4", "target": "n5", "type": "next"}
  ]
}

### Rules
1. Keep `label` EXTREMELY concise.
2. Ensure the graph is connected (no isolated nodes).
3. Use "diverge" nodes to show when multiple possibilities are considered.
4. Use "converge" or "conclusion" nodes to show how the thinking wraps up.
5. STRICTLY output valid JSON only. No markdown fencing if possible, or handle it gracefully.
"""

THINKING_PATH_EXTRACTION_USER_PROMPT = """
Analyze the following AI response and extract its thinking path.

User Question: {question}

AI Response:
{response}
"""
