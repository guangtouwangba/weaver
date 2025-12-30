# Change: Redesign Inbox Page with Enhanced Collection Features

## Why
The current Inbox page is a minimal implementation with basic list and triage layout. Users need a more powerful collection management interface to capture, organize, preview, and assign content from various sources (web pages, videos, PDFs, notes) to their research projects.

## What Changes
- **Rich Item Cards**: Display items with thumbnails, type icons, collection source, and relative timestamps
- **Tag System**: Allow users to categorize items with tags (Strategy, Finance, Product, UX, Market, etc.)
- **Search & Filter**: Enable searching inbox items and filtering by type/tag
- **Content Preview Panel**: Show detailed preview of selected items including content extraction
- **Project Assignment Workflow**: Allow adding items to existing projects or creating new projects
- **New Item Counter**: Display badge showing unread/new item count
- **Collection Source Tracking**: Show how items were collected (Web Extension, manual, etc.)
- **Collection API Endpoint**: Universal API for external clients (Chrome extension, mobile app) to submit content
- **API Key Management**: Allow users to generate/revoke API keys for external collection clients
- **Batch Collection**: Support collecting multiple items in a single API request

## Impact
- **Affected specs**: Creates new `inbox` capability spec
- **Affected code**:
  - `app/frontend/src/app/inbox/` - Inbox page and components
  - `app/frontend/src/app/settings/` - API key management UI
  - `src/research_agent/api/` - Backend API endpoints for inbox items and collection
  - `src/research_agent/db/models/` - Database schema for inbox items, tags, and API keys
- **Future extension**: Backend API designed to support Chrome extension development
- **No breaking changes**: This redesigns an existing page with enhanced functionality

