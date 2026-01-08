# Change: Unify Resource Model

## Why
Currently, content sources are fragmented across multiple data models and APIs:
- **Documents** (`DocumentModel`): PDF, Word, PPT, Audio files with `full_content`, `summary`
- **URL Contents** (`UrlContentModel`): YouTube, Bilibili, Douyin, Web pages with `content`
- **Inbox Items** (`InboxItemModel`): Collection staging with `content`

This fragmentation causes problems:
1. **Code Duplication**: Every feature that processes content (mindmap, summary, chat context, inspiration dock) must handle each type separately
2. **Inconsistent APIs**: `document_ids` vs `url_content_ids` in generation requests
3. **Limited Extensibility**: Adding new content types (audio files, podcasts, images, Notion pages) requires touching many files
4. **Broken Features**: Mindmap generation doesn't work for YouTube videos because it only queries `DocumentModel`

A unified Resource abstraction will make the system extensible and maintainable as new content types are added.

## What Changes

### Phase 1: Backend Resource Abstraction (Minimal Migration)
- **NEW**: Introduce `Resource` domain entity as a unifying interface
- **MODIFIED**: Content loading functions accept resource IDs and resolve to content regardless of source type
- Keep existing database models for backward compatibility
- Add resource registry for type-based content resolution

### Phase 2: Unified Generation API
- **MODIFIED**: Output generation accepts `resource_ids` instead of separate `document_ids` + `url_content_ids`
- **MODIFIED**: Chat context accepts `resource_ids` instead of separate `context_document_ids` + `context_url_ids`
- Frontend unified: single `resources` array in state instead of `documents` + `urlContents`

### Phase 3: Full Model Unification (Future)
- Migrate to single `resources` table with `type` discriminator
- Add new resource types: `audio_file`, `notion_page`, `twitter_thread`, etc.

**This proposal covers Phase 1 only** - establishing the abstraction layer without database migration.

## Impact
- Affected specs: `resources` (NEW), `studio` (MODIFIED)
- Affected code:
  - Backend: New `domain/entities/resource.py` abstraction
  - Backend: New `infrastructure/resource_resolver.py` service
  - Backend: Modified output generation service
  - Backend: Modified chat context loading
  - Frontend: Unified resource state (future phase)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Resource Interface                       │
│  id, type, title, content, metadata, created_at, updated_at │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ implements
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────┴────────┐  ┌────────┴────────┐  ┌───────┴─────────┐
│  DocumentModel  │  │ UrlContentModel │  │ InboxItemModel  │
│  (PDF, Word...)  │  │ (YouTube, Web)  │  │ (Staging Area)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Design Principles
1. **Backward Compatible**: Existing APIs continue to work
2. **Progressive Enhancement**: New unified APIs alongside existing ones
3. **Single Content Accessor**: One function to get content by resource ID
4. **Type-Aware Rendering**: Frontend can render appropriately based on resource type
5. **Extensible**: Adding new resource types = one new adapter class

