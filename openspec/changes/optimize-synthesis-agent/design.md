# Design: Deep Synthesis Agent

## Thinking Process
The user wants the agent to "think" and "review" its work. This implies a Chain-of-Thought (CoT) or Reflection pattern.

We will split the synthesis process into four distinct LLM interactions (chained):

1.  **Reasoning (Domain & Link Analysis)**
    *   **Goal**: Identify the domains of the inputs (e.g., Chemistry, Sociology) and brainstorm potential abstract links *before* writing the final insight.
    *   **Prompt**: "Identify the underlying domains of these inputs. List 3 potential conceptual bridges between them. Don't write the final output yet."
    *   **Output**: Reasoning trace text.

2.  **Drafting**
    *   **Goal**: Create the initial "Consolidated Insight" based on the best conceptual bridge from Step 1.
    *   **Prompt**: "Using the following reasoning [Reasoning Trace], write a consolidated insight..." (Reusing existing JSON structure).
    *   **Output**: Draft JSON.

3.  **Review (Self-Critique)**
    *   **Goal**: Find logical fallacies, weak connections, or hallucinations.
    *   **Prompt**: "Critique this draft. Is the connection forced? Is the science accurate? Rating: 1-5."
    *   **Output**: Critique text.

4.  **Refinement**
    *   **Goal**: Produce the final high-quality output.
    *   **Prompt**: "Given the critique, improve the draft."
    *   **Output**: Final JSON.

## Implementation Details

### `SynthesisAgent` Class
- Refactor `synthesize` method to be an async generator that orchestrates these steps.
- Use `_emit_progress` to communicate "Thinking...", "Drafting...", "Reviewing..." states to the frontend (which supports progress messages).

### Prompts (`research_agent/domain/agents/synthesis_prompts.py`)
- We should separate prompts from the agent class into a dedicated file as they will grow in size and complexity.

## alternatives Considered
- **Single Prompt CoT**: Asking the model to "think step-by-step" in a single call.
    - *Pros*: Faster, cheaper.
    - *Cons*: Less control over the specific "Review" step which user requested. Harder to enforce strict JSON output if reasoning text is mixed in (though libraries helper).
    - *Decision*: Explicit multi-step is better for 'Review' requirement to be explicit ("back and forth" feeling) and higher quality.

## Latency Impact
- Original: ~1 call (3-5s).
- New: ~3-4 calls (10-15s).
- *Mitigation*: The UI already has a "Processing..." state. We will update the progress bar message to keep user engaged ("Analyzing domains...", "Critiquing draft...").
