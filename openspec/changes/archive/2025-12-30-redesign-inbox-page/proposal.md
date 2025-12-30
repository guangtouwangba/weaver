# Change: Redesign Inbox Page with Enhanced Collection Features

![Inbox Design Mockup](uploaded_image_1767076010865.png)

## Why
The current Inbox page is a minimal implementation with basic list and triage layout. Users need a more powerful collection management interface to capture, organize, preview, and assign content from various sources (web pages, videos, PDFs, notes) to their research projects.

## What Changes
- **Rich Item Cards**: Display items with thumbnails, type icons (Article, Video, Note, PDF, Link), collection source, and relative timestamps (e.g., "Added today • Web Article")
- **Tag System**: Allow users to categorize items with colored tags (Strategy, Finance, Product, UX, Market, etc.)
- **Search & Filter**: Full-width search bar in header and "Filter by Type/Tag" dropdown
- **Content Preview Panel**: Detailed view with type badge, source info ("Collected via..."), content skeleton/preview, and "Read Full Article" button
- **Project Assignment Footer**: Distinct "Add to Existing Project" dropdown and large "Create New Project" action area at the bottom of the preview
- **New Item Counter**: "COLLECTED ITEMS" header with count badge (e.g., "12 New")
- **Collection Source Tracking**: Explicit display of source (Web Extension, key-based, manual)
- **Edit & Delete Actions**: Quick access edit (pencil) and delete (trash) icons in the preview header
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

