## 1. Frontend Implementation
- [ ] 1.1 Install and configure `next-intl` in `app/frontend/package.json` and `next.config.js` (if applicable) or middleware.
- [ ] 1.2 Create locale files (en.json, zh.json) in `app/frontend/messages` or `app/frontend/public/locales`.
- [ ] 1.3 Create a `LanguageSwitcher` component.
- [ ] 1.4 Update root layout/provider to handle locale state.
- [ ] 1.5 Replace hardcoded text in main navigation and `AssistantPanel` with `t()` calls.

## 2. Backend Implementation
- [ ] 2.1 Update `BaseAgent.generate` signature to accept `language` parameter (default "en").
- [ ] 2.2 Update `SummaryAgent`, `MindmapAgent`, `FlashcardAgent`, `SynthesisAgent` to propagate `language`.
- [ ] 2.3 Update `rag_prompt.py` and other prompt files to use `{language}` in system/user instructions.
- [ ] 2.4 Update backend API endpoints (likely in `app/routers` or `controllers`) to read `Accept-Language` header or `language` body param and pass it to agents.

## 3. Verification
- [ ] 3.1 Verify UI switches language when `LanguageSwitcher` is toggled.
- [ ] 3.2 Verify `SummaryAgent` generates summary in Chinese when Chinese is selected.
- [ ] 3.3 Verify RAG chat answers in Chinese when Chinese is selected.
