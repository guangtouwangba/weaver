"""Prompt templates for the Synthesis Agent.

Contains prompts for the multi-step synthesis process:
1. Reasoning (Domain & Link Analysis)
2. Drafting (Initial Insight)
3. Review (Self-Critique)
4. Refinement (Final Output)
"""

# =============================================================================
# REASONING PROMPTS - Domain & Link Analysis
# =============================================================================

REASONING_PROMPT = """You are an expert analyst. Your task is to analyze these inputs and identify potential connections BEFORE writing any final output.

**Your Goals:**
1. Identify the **domain(s)** of each input (e.g., Chemistry, Physics, Sociology, History, Art, Technology).
2. List **3 potential conceptual bridges** between these seemingly distinct items.
3. For each bridge, explain WHY it could be a meaningful connection.

**Do NOT write the final synthesis yet.** Focus only on analysis and brainstorming.

Output your analysis as plain text in this structure:

## Domain Analysis
- Input 1: [Domain(s)]
- Input 2: [Domain(s)]

## Potential Bridges
1. [Bridge Name]: [Explanation of why this connection is meaningful]
2. [Bridge Name]: [Explanation]
3. [Bridge Name]: [Explanation]

## Recommended Angle
Based on my analysis, the strongest bridge is [X] because [reason].

---

Here are the inputs to analyze:

{inputs}
"""

# =============================================================================
# DRAFTING PROMPTS - Initial Insight Generation
# =============================================================================

DRAFTING_PROMPTS = {
    "connect": """You are an expert analyst. Based on the following reasoning analysis, write a consolidated insight identifying hidden connections and common themes.

**Reasoning Analysis:**
{reasoning}

**Instructions:**
Use the recommended angle from the reasoning to write a compelling connection. Focus on structural similarities, shared principles, or latent links.

Output ONLY a valid JSON object with this structure:
{{
    "title": "A title highlighting the connection (e.g., 'The Link between X and Y')",
    "main_insight": "The core connection or shared theme found (2-3 sentences)",
    "recommendation": "How to leverage this connection",
    "key_risk": "Potential misinterpretations or false equivalences",
    "supporting_themes": ["shared theme 1", "shared theme 2"],
    "confidence": "high" | "medium" | "low"
}}

Here are the original inputs:

{inputs}
""",
    "inspire": """You are a creative muse. Based on the following reasoning analysis, generate a creative leap or new perspective.

**Reasoning Analysis:**
{reasoning}

**Instructions:**
Use the recommended angle to reframe or re-imagine the inputs. How does one idea change the meaning of the other?

Output ONLY a valid JSON object with this structure:
{{
    "title": "An inspiring title (e.g., 'Reframing X through Y')",
    "main_insight": "The new perspective or creative leap generated (2-3 sentences)",
    "recommendation": "A creative direction to explore",
    "key_risk": "Feasibility or practicality concerns",
    "supporting_themes": ["new perspective 1", "new perspective 2"],
    "confidence": "high" | "medium" | "low"
}}

Here are the original inputs:

{inputs}
""",
    "debate": """You are a critical thinker. Based on the following reasoning analysis, identify conflicts, tensions, and trade-offs.

**Reasoning Analysis:**
{reasoning}

**Instructions:**
Use the recommended angle to explore where the inputs disagree or create tension. Which argument is more robust in which context?

Output ONLY a valid JSON object with this structure:
{{
    "title": "A provocative title (e.g., 'X vs Y: The Tension')",
    "main_insight": "The core conflict or tension identified (2-3 sentences)",
    "recommendation": "How to resolve or navigate this tension",
    "key_risk": "Biases or overlooked nuances",
    "supporting_themes": ["tension 1", "disagreement 2"],
    "confidence": "high" | "medium" | "low"
}}

Here are the original inputs:

{inputs}
""",
}

# =============================================================================
# REVIEW PROMPTS - Self-Critique
# =============================================================================

REVIEW_PROMPT = """You are a critical reviewer. Your task is to critique the following synthesis draft.

**Draft to Review:**
{draft}

**Original Inputs Used:**
{inputs}

**Critique the draft on these dimensions:**
1. **Logical Soundness**: Is the connection forced or genuinely insightful?
2. **Accuracy**: Are there any scientific or factual errors?
3. **Depth**: Is this a surface-level observation or a deep insight?
4. **Actionability**: Is the recommendation useful?

**Output your critique as plain text:**

## Critique
- Logical Soundness: [Rating 1-5] - [Explanation]
- Accuracy: [Rating 1-5] - [Explanation]
- Depth: [Rating 1-5] - [Explanation]
- Actionability: [Rating 1-5] - [Explanation]

## Specific Issues
[List any specific problems that should be fixed]

## Suggested Improvements
[List concrete improvements to make]
"""

# =============================================================================
# REFINEMENT PROMPTS - Final Output
# =============================================================================

REFINEMENT_PROMPT = """You are an expert analyst tasked with improving a synthesis draft based on critique.

**Original Draft:**
{draft}

**Critique Received:**
{critique}

**Instructions:**
Address the issues raised in the critique. Improve the logical soundness, accuracy, depth, and actionability of the insight. Keep the same JSON structure.

Output ONLY a valid JSON object with this structure:
{{
    "title": "Improved title",
    "main_insight": "Improved core insight (2-3 sentences)",
    "recommendation": "Improved recommendation",
    "key_risk": "Improved risk assessment",
    "supporting_themes": ["theme 1", "theme 2"],
    "confidence": "high" | "medium" | "low"
}}
"""
