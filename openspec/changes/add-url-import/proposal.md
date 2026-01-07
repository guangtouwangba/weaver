# Change: Add URL Import Capability

## Why
Users need to import content from URLs (web pages, YouTube videos, Bilibili, Douyin) into the system. Currently, the Import Source dialog has a URL input field but lacks backend processing. A standalone URL extractor module will enable content parsing that can be **reused across Inbox collection, Studio import, and future features**.

## What Changes
- Add new `url-extractor` capability as a **standalone, reusable backend module**
- Support platform detection: YouTube, Bilibili, Douyin, generic web pages
- Extract full article text for web pages using trafilatura
- Extract transcripts for video platforms using youtube-transcript-api (YouTube) and platform-specific APIs
- Async processing via ARQ worker (consistent with document processing)
- Pre-defined platform icons with fallback to generic web icon
- Frontend integration with existing ImportSourceDialog

## Impact
- Affected specs: `url-extractor` (NEW)
- Affected code:
  - Backend: New `src/research_agent/infrastructure/url_extractor/` module
  - Backend: New ARQ task for URL processing
  - Backend: Generic API endpoint `/api/v1/url/extract`
  - Frontend: Wire up `onUrlImport` in ImportSourceDialog
  - Frontend: Platform-specific icon utility

> **Note:** Inbox-specific integration will be done separately. This module is designed to be consumed by both Inbox and Studio.

