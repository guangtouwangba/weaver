# Tasks: Deep Synthesis Agent

## Phase 1: Preparation
- [x] Create `src/research_agent/domain/agents/synthesis_prompts.py` to hold new prompt templates.
- [x] Refactor `SynthesisAgent` to import prompts from the new file.

## Phase 2: Implementation of Reasoning Pipeline
- [x] Implement `_reason_about_inputs` method in `SynthesisAgent` with domain analysis prompt.
- [x] Implement `_draft_synthesis` method using reasoning context.
- [x] Implement `_review_draft` method for self-critique.
- [x] Implement `_refine_draft` method to produce final output.

## Phase 3: Orchestration
- [x] Update `synthesize` async generator to chain these steps deeply.
- [x] Ensure `_emit_progress` is called with appropriate messages ("Thinking...", "Reviewing...") at each step.

## Phase 4: Validation
- [x] Add unit test for `SynthesisAgent` verifying the multi-step execution flow (mocking LLM).
  - Note: Test created but blocked by langchain environment issue (pydantic_v1 module missing). Test structure is correct.
- [ ] Verify manually on canvas that progress messages update and result quality is improved.
