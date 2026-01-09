# Design: Refactor Prompts to Jinja2 Templates

## Context
The backend currently has **~25 prompt templates** scattered across:
- `infrastructure/llm/prompts/rag_prompt.py` - RAG system prompts, intent classification, generation prompts
- `domain/agents/` - Agent-specific prompts (mindmap, summary, flashcard, article, action_list, synthesis)
- `application/graphs/` - Graph workflow prompts (rag_graph, mindmap_graph)
- `domain/services/memory_service.py` - Conversation summarization prompts
- `worker/tasks/document_processor.py` - Document processing prompts

These prompts use Python f-strings or `.format()` for variable substitution.

## Goals
- **Separation of concerns**: Prompts as data, not code
- **Maintainability**: Edit prompts without modifying Python files
- **Reusability**: Share common prompt components (guidelines, output formats)
- **Testability**: Validate templates independently of runtime
- **Future i18n**: Enable localization of prompts

## Non-Goals
- Prompt versioning system (future enhancement)
- A/B testing for prompts (future enhancement)
- UI-based prompt editing (future enhancement)

## Decisions

### Decision 1: Template Directory Structure
**Choice**: Flat structure with namespace prefixes
```
prompts/templates/
├── _base/                 # Shared partials
│   ├── guidelines.j2
│   └── json_output.j2
├── rag/
│   ├── system.j2
│   ├── memory_aware_system.j2
│   ├── intent_classification.j2
│   ├── long_context_system.j2
│   └── generation/
│       ├── factual.j2
│       ├── conceptual.j2
│       └── ...
├── agents/
│   ├── mindmap/
│   │   ├── system.j2
│   │   ├── explain_node.j2
│   │   └── expand_node.j2
│   ├── summary/
│   │   ├── system.j2
│   │   └── generation.j2
│   ├── flashcard.j2
│   ├── article/
│   │   ├── system.j2
│   │   └── generation.j2
│   └── action_list/
│       ├── system.j2
│       └── generation.j2
├── synthesis/
│   ├── reasoning.j2
│   ├── drafting/
│   │   ├── connect.j2
│   │   ├── inspire.j2
│   │   └── debate.j2
│   ├── review.j2
│   └── refinement.j2
├── graph/
│   ├── mindmap_root.j2
│   └── mindmap_branches.j2
└── services/
    └── conversation_summary.j2
```

**Rationale**: Mirrors the code structure, easy to find templates.

### Decision 2: Template Loading API
**Choice**: Simple loader class with caching

```python
from research_agent.infrastructure.llm.prompts import PromptLoader

# Initialize once at startup
prompt_loader = PromptLoader()

# Usage in agents
system_prompt = prompt_loader.render("agents/summary/system.j2")
user_prompt = prompt_loader.render(
    "agents/summary/generation.j2",
    title=document_title,
    content=document_content,
)
```

**Alternatives Considered**:
1. **Decorator-based**: `@prompt("rag/system.j2")` - Too magical, harder to debug
2. **Global singleton**: `prompts.render(...)` - Less explicit, testing issues
3. **Dependency injection**: Pass loader to each agent - Chosen approach, testable

### Decision 3: Template Syntax Conventions
**Choice**: Use Jinja2 defaults with these conventions:
- Variables: `{{ variable_name }}`
- Includes: `{% include '_base/guidelines.j2' %}`
- Conditionals: `{% if chat_history %}...{% endif %}`
- Loops: `{% for item in items %}...{% endfor %}`
- Escape for JSON: Use raw blocks for JSON examples

Example:
```jinja
{# agents/summary/generation.j2 #}
Analyze the following document and create an executive summary.

Document Title: {{ title }}

Document Content:
{{ content }}

{% include '_base/guidelines.j2' %}

{% raw %}
Respond with a JSON object in this exact format:
{
  "summary": "...",
  "keyFindings": [...]
}
{% endraw %}
```

### Decision 4: Migration Strategy
**Choice**: Incremental migration with backward compatibility

Phase 1: Infrastructure (this change)
- Create PromptLoader class
- Add template directory structure
- Migrate 3 high-traffic templates as proof of concept:
  - `rag/system.j2`
  - `agents/summary/generation.j2`
  - `synthesis/reasoning.j2`

Phase 2: Full migration (follow-up change)
- Migrate remaining templates
- Remove old Python string constants
- Add template validation in CI

**Rationale**: Lower risk, faster feedback loop.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Runtime template loading errors | Validate all templates at startup; fail-fast |
| Performance overhead | Cache compiled templates; Jinja2 is fast |
| Developer unfamiliarity with Jinja2 | Minimal Jinja2 features used; document patterns |
| Breaking existing prompts | Exact string comparison in tests; incremental migration |

## Migration Plan

1. Add `jinja2` dependency (already present via FastAPI templates)
2. Create `PromptLoader` class with template directory configuration
3. Create initial template files for Phase 1
4. Update agents to use `PromptLoader`
5. Add integration tests for template rendering
6. Document template conventions in `docs/prompts.md`

## Open Questions

1. **Template hot-reloading in development?** - Consider for DX, not blocking
2. **Should we support template variants (e.g., by model)?** - Future enhancement
