# Tasks: Refactor Prompts to Jinja2 Templates

## 1. Infrastructure Setup
- [ ] 1.1 Create `prompts/templates/` directory structure
- [ ] 1.2 Implement `PromptLoader` class with Jinja2 environment
- [ ] 1.3 Add template caching and error handling
- [ ] 1.4 Add startup validation for all templates

## 2. Template Migration (Phase 1 - Proof of Concept)
- [ ] 2.1 Create `_base/` shared partials (guidelines, json_output)
- [ ] 2.2 Migrate `rag/system.j2` from SYSTEM_PROMPT in rag_prompt.py
- [ ] 2.3 Migrate `agents/summary/` templates
- [ ] 2.4 Migrate `synthesis/reasoning.j2`

## 3. Agent Integration
- [ ] 3.1 Inject `PromptLoader` into agent constructors
- [ ] 3.2 Update `SummaryAgent` to use template loading
- [ ] 3.3 Update `SynthesisAgent` to use template loading
- [ ] 3.4 Update RAG pipeline to use template loading

## 4. Testing
- [ ] 4.1 Add unit tests for `PromptLoader`
- [ ] 4.2 Add template rendering tests with sample variables
- [ ] 4.3 Add integration tests comparing old vs new prompt output

## 5. Documentation
- [ ] 5.1 Document template conventions in backend docs
- [ ] 5.2 Add inline comments in template files
