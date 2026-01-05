# Change: Support System Internationalization

## Why
Users need to interact with the system in their preferred language. The system currently lacks explicit internationalization support, defaulting to English. This change ensures that both the user interface and AI-generated content (summaries, mindmaps, answers) adhere to the user's selected language.

## What Changes
- **Frontend**:
  - Implement `next-intl` for standardizing UI text translation.
  - storing the user's locale in a cookie (`NEXT_LOCALE`).
  - Add a language switcher component to the UI.
  - Translate key UI elements (navigation, common actions).
- **Backend API**:
  - Update API endpoints to accept a `language` parameter (or extract from headers).
- **Agents & Prompts**:
  - Update `BaseAgent` and specific agents (`SummaryAgent`, `MindmapAgent`, `FlashcardAgent`, `SynthesisAgent`) to accept `language`.
  - Update `RAGPrompt` and other prompt templates to explicitly instruct the LLM to generate content in the specified language.

## Impact
- **Affected Specs**:
  - `frontend`: New requirements for i18n.
  - `agents`: New requirements for language-aware generation.
- **Affected Code**:
  - `app/frontend/package.json` (New dependency).
  - `app/frontend/src/**` (UI components wrapped in translations).
  - `app/backend/src/research_agent/infrastructure/llm/prompts/` (Prompt templates).
  - `app/backend/src/research_agent/domain/agents/` (Agent signatures).
