# Change: Add Universal Inbox Collection API

## Why
The Inbox needs a robust, well-documented external API that enables content collection from various sources (Chrome extension, iOS Shortcuts, mobile apps, third-party integrations). This API must be secure, extensible, and support the full content lifecycle from collection to project assignment.

## What Changes
- Enhance the existing `/api/inbox/collect` endpoint with improved schema validation and error handling
- Add webhook notification support for real-time collection events
- Implement API key management UI in settings
- Add content preview functionality in the Inbox page (based on design mockup)
- Implement "Add to Project" workflow with existing project dropdown + create new project option
- Support platform-specific metadata for YouTube, web articles, PDFs, and notes

## Impact
- Affected specs: `inbox`
- Affected code:
  - Backend: `app/backend/src/research_agent/api/v1/inbox.py`
  - Backend: `app/backend/src/research_agent/application/dto/inbox.py`
  - Frontend: `app/frontend/src/app/inbox/page.tsx`
  - Frontend: `app/frontend/src/components/inbox/*`
  - Frontend: `app/frontend/src/app/settings/page.tsx` (API key management)

