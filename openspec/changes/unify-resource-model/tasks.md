# Tasks: Unify Resource Model (Phase 1)

## 1. Domain Layer

- [x] 1.1 Create `ResourceType` enum in `domain/entities/resource.py`
- [x] 1.2 Create `Resource` dataclass with unified interface
- [ ] 1.3 Add `to_resource()` method to `Document` entity (deferred - adapters in ResourceResolver are sufficient)
- [x] 1.4 Add type annotations and docstrings

## 2. Infrastructure Layer

- [x] 2.1 Create `infrastructure/resource_resolver.py` with `ResourceResolver` class
- [x] 2.2 Implement `resolve()` method with type-based dispatch
- [x] 2.3 Implement `resolve_many()` method with batch optimization
- [x] 2.4 Implement `get_content()` convenience method
- [x] 2.5 Add adapter for `DocumentModel` to `Resource`
- [x] 2.6 Add adapter for `UrlContentModel` to `Resource`
- [ ] 2.7 Add unit tests for `ResourceResolver` (deferred to follow-up)

## 3. Service Layer Integration

- [x] 3.1 Modify `OutputGenerationService._load_document_content()` to use `ResourceResolver`
- [ ] 3.2 Accept `resource_ids` parameter alongside existing `document_ids` + `url_content_ids` (Phase 2)
- [x] 3.3 Update logging to show resource types being loaded
- [x] 3.4 Ensure backward compatibility with existing API calls

## 4. Chat Context Integration

- [x] 4.1 Modify `StreamMessageUseCase` to use `ResourceResolver` for context loading
- [ ] 4.2 Unify `context_document_ids` and `context_url_ids` handling (Phase 2 - API change)
- [ ] 4.3 Add tests for unified context loading (deferred to follow-up)

## 5. API Layer (Optional - New Endpoints)

- [ ] 5.1 Add `GET /api/v1/projects/{project_id}/resources` endpoint (Phase 2)
- [ ] 5.2 Return unified resource list (documents + urls merged) (Phase 2)
- [ ] 5.3 Add `resource_ids` field to `GenerateOutputRequest` DTO (Phase 2)

## 6. Documentation

- [x] 6.1 Update CHANGELOG.md with architecture change
- [x] 6.2 Add inline documentation for new components
- [ ] 6.3 Update API documentation if endpoints change (Phase 2)

## Dependencies

- Tasks 1.x must complete before 2.x
- Tasks 2.x must complete before 3.x and 4.x
- Tasks 3.x and 4.x can run in parallel
- Task 5.x is optional for Phase 1

## Verification

After completion:
1. Import a YouTube video
2. Right-click on canvas then Generate Mind Map
3. Verify mindmap is generated from video transcript
4. Verify existing PDF document generation still works

## Phase 1 Completion Summary

**Completed:**
- ResourceType enum with content-category based types (VIDEO, AUDIO, DOCUMENT, etc.)
- Resource dataclass with unified interface
- ResourceResolver service with resolve(), resolve_many(), get_content(), get_combined_content()
- Adapters for DocumentModel and UrlContentModel
- OutputGenerationService integration (uses ResourceResolver for content loading)
- StreamMessageUseCase integration (uses ResourceResolver for URL context)
- CHANGELOG.md updated

**Deferred to Phase 2:**
- Unified `resource_ids` API parameter
- New `/resources` endpoint
- Frontend unified resource state

**Deferred to follow-up:**
- Unit tests for ResourceResolver
