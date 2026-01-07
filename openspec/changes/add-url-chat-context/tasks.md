# Tasks: Add URL Content to Chat Context

## 1. Frontend: Chat Drop Handler Extension

- [x] 1.1 Extend `AssistantPanel.handleDrop` to accept `type: 'url'` drag data
- [x] 1.2 Add URL-specific fields to `contextNodes` state (platform, contentType, thumbnailUrl)
- [x] 1.3 Handle extraction status (show loading state if content not ready)

## 2. Frontend: Context Chip Component

- [x] 2.1 Create `UrlContextChip` component with platform icon and title
- [x] 2.2 Add platform icons for YouTube (red), Bilibili (blue), Douyin (black), Web (gray globe)
- [x] 2.3 Display loading spinner on chip when extraction is pending
- [x] 2.4 Add remove button functionality

## 3. Frontend: Resource Sidebar Drag Data

- [x] 3.1 Extend URL item drag data to include `id` (url_content_id)
- [x] 3.2 Include `content` field in drag data when available
- [x] 3.3 Include `status` field to indicate extraction state

## 4. Backend: Chat API Extension

- [x] 4.1 Add `context_url_ids: list[str] | None` to `ChatRequest` DTO
- [x] 4.2 Validate URL content IDs exist and belong to project/user
- [x] 4.3 Update API documentation (via OpenAPI auto-gen from Pydantic)

## 5. Backend: RAG Context Injection

- [x] 5.1 Fetch URL content records by IDs in chat service
- [x] 5.2 Inject URL content text into RAG context alongside document chunks
- [x] 5.3 Handle truncation for very long transcripts/articles (50k char limit)
- [x] 5.4 Include URL source metadata for citation generation

## 6. Frontend: Chat Message Citations

- [ ] 6.1 Extend citation chip to handle URL sources (deferred - requires citation system refactor)
- [ ] 6.2 Click URL citation opens original URL in new tab (deferred)
- [ ] 6.3 Display platform icon on URL citation chips (deferred)

> **Note:** Tasks 6.1-6.3 are deferred. The current implementation injects URL content as context with source information, allowing the AI to naturally reference the content in its response. Formal URL citation chips would require changes to the existing citation system.

## 7. Integration Testing

- [ ] 7.1 Test drag YouTube video from sidebar to chat
- [ ] 7.2 Test drag web article from sidebar to chat
- [ ] 7.3 Test mixed context (document + URL)
- [ ] 7.4 Test pending extraction shows loading state
- [ ] 7.5 Test failed extraction shows error state

> **Note:** Integration tests require running services and will be validated during manual testing.
