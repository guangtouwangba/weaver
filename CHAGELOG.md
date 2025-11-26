# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed - MVP Scope Cleanup (2025-11-26)

**Frontend cleanup to align with MVP scope (PDF-only, Canvas-focused)**

- **Removed** `PodcastView.tsx` - AI-generated podcast view (out of MVP scope)
- **Removed** `WriterView.tsx` - Concept mixer writing view (out of MVP scope)
- **Simplified** `app/frontend/src/app/studio/page.tsx` (1560 → 876 lines, -44%):
  - Removed multi-media player support (Video/Audio)
  - Removed multi-tab system (Podcast/Writer/Slides/Flashcards)
  - Removed Canvas Copilot AI panel (out of MVP scope)
  - Removed Quiet Mode toggle
  - Simplified resource list to PDF-only
  - Simplified AI Assistant panel to basic chat interface
  - Retained core Canvas functionality with nodes and connections
  - Retained PDF text drag-and-drop to Canvas feature

**Documentation**
- Added `docs/product design/MVP_Scope.md` - MVP feature specification document

