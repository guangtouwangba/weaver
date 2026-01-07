# Tasks: Add Magic Cursor Generation Logic

## Backend Implementation

### 1. Domain Layer
- [x] 1.1 Add `ARTICLE` and `ACTION_LIST` to `OutputType` enum in `domain/entities/output.py`
- [x] 1.2 Create `ArticleData` dataclass for article output structure
- [x] 1.3 Create `ActionListData` dataclass for action list output structure
- [x] 1.4 Create `ArticleAgent` in `domain/agents/article_agent.py`
- [x] 1.5 Create `ActionListAgent` in `domain/agents/action_list_agent.py`

### 2. Application Layer
- [x] 2.1 Add article generation handler in `OutputGenerationService._run_article_generation()`
- [x] 2.2 Add action list generation handler in `OutputGenerationService._run_action_list_generation()`
- [x] 2.3 Update service routing to handle new output types

## Frontend Implementation

### 3. API Integration
- [x] 3.1 Update `outputsApi.generate()` type to include `'article' | 'action_list'`
- [x] 3.2 Add `ArticleData` and `ActionListData` TypeScript types

### 4. Intent Menu Connection
- [x] 4.1 Implement `handleIntentAction` to call API with node data
- [x] 4.2 Add loading state to IntentMenu or selection area
- [ ] 4.3 Handle generation errors with toast notifications
- [x] 4.4 Add max 50 nodes validation with toast warning

### 5. Result Display
- [x] 5.1 Create result node on canvas after generation completes
- [x] 5.2 Position result node at bottom-right of selection + 20px offset
- [x] 5.3 Apply Super Card styling (article vs checklist)
- [x] 5.4 Store snapshot context in node metadata

### 6. Super Card Interaction
- [x] 6.1 Implement Document Card click → open modal with article content
- [x] 6.2 Implement Ticket Card click → open modal with action items
- [x] 6.3 Add rich text editing for Document Card content
- [x] 6.4 Add action item CRUD in Ticket Card modal
- [x] 6.5 Implement checkbox toggle on canvas (without opening modal)
- [ ] 6.6 Persist edits to backend on save

## Validation
- [ ] 7.1 Test article generation with 2-3 nodes selected
- [ ] 7.2 Test action list generation with notes containing tasks
- [ ] 7.3 Test error handling (empty selection, API failure)
- [ ] 7.4 Verify WebSocket streaming works correctly
- [ ] 7.5 Test Super Card click to open modal
- [ ] 7.6 Test editing and saving changes
- [ ] 7.7 Test checkbox toggle on Ticket Card canvas view

