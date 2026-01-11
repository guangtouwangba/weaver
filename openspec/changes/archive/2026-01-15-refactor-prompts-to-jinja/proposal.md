# Change: Refactor Prompt Templates to Jinja2 Files

## Why
Currently, all prompt templates are defined as Python string constants scattered across multiple files (agents, graphs, services). This makes it hard to:
1. Edit prompts without touching Python code
2. Version and track prompt changes separately
3. Reuse prompt components across agents
4. Support i18n/localization of prompts in the future
5. Enable non-developers to iterate on prompt engineering

Jinja2 templates provide a mature, well-supported templating solution with:
- Separation of concerns (prompts vs. logic)
- Template inheritance and includes for DRY patterns
- Built-in escaping and formatting
- Easy testing and validation

## What Changes
- Create `app/backend/src/research_agent/infrastructure/llm/prompts/templates/` directory for `.j2` files
- Migrate all hardcoded prompt strings to Jinja2 template files
- Implement `PromptLoader` utility for loading and rendering templates
- Refactor agents/graphs/services to use the new template loading system
- Add template validation on startup

## Impact
- Affected specs: `agents` (new capability for prompt management)
- Affected code:
  - `app/backend/src/research_agent/infrastructure/llm/prompts/` (new module)
  - `app/backend/src/research_agent/domain/agents/*.py` (all agents)
  - `app/backend/src/research_agent/application/graphs/*.py` (rag_graph, mindmap_graph)
  - `app/backend/src/research_agent/domain/services/memory_service.py`
  - `app/backend/src/research_agent/worker/tasks/document_processor.py`
