# Tasks: Deep Synthesis Agent

## Phase 1: Preparation
- [ ] Create `src/research_agent/domain/agents/synthesis_prompts.py` to hold new prompt templates.
- [ ] Refactor `SynthesisAgent` to import prompts from the new file.

## Phase 2: Implementation of Reasoning Pipeline
- [ ] Implement `_reason_about_inputs` method in `SynthesisAgent` with domain analysis prompt.
- [ ] Implement `_draft_synthesis` method using reasoning context.
- [ ] Implement `_review_draft` method for self-critique.
- [ ] Implement `_refine_draft` method to produce final output.

## Phase 3: Orchestration
- [ ] Update `synthesize` async generator to chain these steps deeply.
- [ ] Ensure `_emit_progress` is called with appropriate messages ("Thinking...", "Reviewing...") at each step.

## Phase 4: Validation
- [ ] Add unit test for `SynthesisAgent` verifying the multi-step execution flow (mocking LLM).
- [ ] Verify manually on canvas that progress messages update and result quality is improved.
