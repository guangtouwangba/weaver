# Design: URL Content in Chat Context

## Context
The Studio chat currently supports dragging documents and canvas nodes into the chat input to provide context for AI queries. The URL extractor module (from `add-url-import`) extracts content from YouTube, Bilibili, Douyin, and web pages. Users expect to ask questions like "What does this video talk about?" by dragging URL content into the chat.

**Constraints:**
- Solo developer: minimize new abstractions
- Reuse existing URL extractor infrastructure
- Consistent UX with existing document drag-to-chat flow

## Goals / Non-Goals

**Goals:**
- Enable dragging any URL content from Resource Sidebar into chat
- Use extracted content (transcript/article text) as RAG context
- Display platform-appropriate visual chips in chat input
- Support all platforms: YouTube, Bilibili, Douyin, web pages
- Graceful handling when content not yet extracted

**Non-Goals:**
- Video playback within chat interface
- Real-time transcript generation from audio (Whisper)
- Direct URL paste into chat (future enhancement)

## Decisions

### 1. Frontend: URL Drop Handling

**Decision:** Extend `handleDrop` in `AssistantPanel.tsx` to handle `type: 'url'` data.

```typescript
// In handleDrop
else if (data.type === 'url') {
  if (!contextNodes.some(n => n.id === data.id)) {
    setContextNodes(prev => [...prev, {
      id: data.id,
      title: data.title,
      content: `[${data.platform}] ${data.title}`,
      platform: data.platform,
      contentType: data.contentType,
      thumbnailUrl: data.thumbnailUrl,
      sourceMessageId: undefined
    }]);
  }
}
```

**Rationale:** Minimal change to existing drop handler. Reuses `contextNodes` state structure with optional platform field.

### 2. Context Chip Display

**Decision:** Create platform-aware context chip component that shows:
- Platform icon (YouTube red, Bilibili blue, Douyin black, Globe for web)
- Truncated title
- Remove button

```typescript
interface ContextChip {
  id: string;
  title: string;
  type: 'document' | 'node' | 'url';
  platform?: 'youtube' | 'bilibili' | 'douyin' | 'web';
  thumbnailUrl?: string;
}
```

**Rationale:** Extends existing chip display with platform differentiation. Users can visually identify context type.

### 3. Backend: Context Parameter

**Decision:** Extend `/api/v1/projects/{id}/chat` to accept `url_content_ids: list[str]` parameter.

```python
class ChatRequest(BaseModel):
    query: str
    context_document_ids: list[str] | None = None
    context_node_ids: list[str] | None = None
    context_url_ids: list[str] | None = None  # NEW
```

**Rationale:** Consistent with existing context parameter pattern. Allows mixed context (documents + URLs).

### 4. RAG Context Injection

**Decision:** Fetch URL content text and inject into RAG retrieval context.

```python
# In chat service
url_contents = await url_content_repo.get_by_ids(context_url_ids)
for url_content in url_contents:
    if url_content.content:
        context_chunks.append({
            "source_type": "url",
            "source_id": str(url_content.id),
            "platform": url_content.platform,
            "title": url_content.title,
            "content": url_content.content[:MAX_CONTEXT_LENGTH]
        })
```

**Rationale:** Treats URL content similar to document chunks. Content is truncated to fit context window.

### 5. On-the-Fly Extraction Fallback

**Decision:** If URL content status is "pending" or "processing", show loading state in frontend. If "failed", show error chip but still allow sending query (AI will acknowledge missing context).

**Frontend Flow:**
1. User drops URL item
2. Check if `content` is available in drag data
3. If available, add to context immediately
4. If not, show "Extracting..." state on chip
5. Poll `/api/v1/url/extract/{id}` for completion
6. Update chip when ready

**Rationale:** Graceful degradation. Users don't need to wait for extraction before starting a conversation.

### 6. Drag Data Extension

**Decision:** Extend URL item drag data in `ResourceSidebar.tsx` to include:
- `id`: URL content ID
- `content`: Extracted text (if available)
- All existing metadata (platform, title, thumbnail, etc.)

**Rationale:** Allows immediate context display without additional API call when content is already extracted.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Large transcripts exceed context window | Truncate to 50,000 characters (configurable) |
| Extraction delay frustrates users | Show loading state with progress indicator |
| Mixed document + URL context is confusing | Clear visual differentiation via platform icons |
| Bilibili/Douyin often lack transcripts | Use video description as fallback (per url-extractor spec) |

## Migration Plan

1. Extend frontend `AssistantPanel.handleDrop` for URL type
2. Add platform-aware context chip component
3. Extend `ResourceSidebar` URL item drag data to include content
4. Add `context_url_ids` to chat API endpoint
5. Extend chat service to fetch and inject URL content
6. Update chat response to include URL source citations

**Rollback:** Remove `context_url_ids` parameter; frontend changes are additive.

## Open Questions

1. **Citation format for URL sources:** Should citations link back to the original URL or the source panel?
   - *Proposed:* Link to original URL (opens in new tab) since we don't have a dedicated URL content viewer yet.

2. **Context priority:** When both documents and URLs are provided, which takes precedence?
   - *Proposed:* Merge all context; let LLM determine relevance.

