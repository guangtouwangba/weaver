# Change: Refactor Mindmap Agent to Direct Generation Algorithm

## Why
The original DocTree algorithm (chunking → semantic parsing → clustering → aggregation) was complex and made many LLM calls. With modern LLMs having large context windows (Gemini 2.5 Flash: 1M tokens), we can simplify to a **2-step direct generation** approach that:
1. Uses full document context for better understanding
2. Reduces LLM calls from N+log(N) to just **2 calls**
3. Produces better results by avoiding information loss from chunking

## What Changes
- **BREAKING**: Replace the current top-down mindmap generation with a 2-step direct approach
- **Phase 1: Direct Generation** - Single LLM call generates the entire mindmap from full text
- **Phase 2: Refinement** - Single LLM call cleans up duplicates and improves structure
- **Source Reference Preservation**: LLM includes `[Page X]` or `[MM:SS]` markers for navigation
- Support for large context windows (up to 500K tokens by default, configurable)
- Output format: **Markdown outline** (simpler than Mermaid, easier to parse)
- Multi-language support: Chinese (default) and English prompts
- **Token optimization**: From N+log(N) LLM calls to just **2 calls total**

## Impact
- Affected specs: `agents`
- Affected code:
  - `app/backend/src/research_agent/application/graphs/mindmap_graph.py` (complete rewrite)
  - `app/backend/src/research_agent/domain/agents/mindmap_agent.py` (update to use new graph)
  - New modules: `direct_generate.py`, `refine_output.py`
  - Remove: chunker, semantic_parser, tree_aggregation, clustering, embedding modules
