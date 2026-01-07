# Change: Add URL Content to Chat Context

## Why
Users want to ask questions about imported URL content (YouTube videos, Bilibili videos, Douyin videos, web articles) by dragging them into the AI assistant chat. Currently, the chat only accepts documents and canvas nodes as context. Extending this to URL content enables a unified "drag to ask" experience across all source types in the Resource Sidebar.

## What Changes
- Extend chat drop handler to accept URL content items from Resource Sidebar
- Display URL content as context chips in chat input (with platform icons)
- Backend RAG endpoint accepts URL content IDs as additional context
- Include URL content text (article body or video transcript) in retrieval context
- Support all platforms: YouTube, Bilibili, Douyin, and generic web pages
- On-the-fly extraction fallback if content not yet extracted (with loading state)

## Impact
- Affected specs: `studio` (chat interface requirements)
- Affected code:
  - Frontend: `AssistantPanel.tsx` - extend `handleDrop` for URL type
  - Frontend: Context chip component for URL items with platform icons
  - Backend: `/api/v1/projects/{id}/chat` - accept `url_content_ids` parameter
  - Backend: RAG retrieval to include URL content text

