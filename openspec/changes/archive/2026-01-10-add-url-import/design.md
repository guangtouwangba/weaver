# Design: URL Import Module

## Context
The system currently supports file uploads (PDF, DOCX) but lacks URL-based content import. Users paste URLs into the Import Source dialog, but no backend processing exists. This design introduces a modular URL extractor that can be extended to support more platforms.

**Prerequisites (discovered during analysis):**
- ARQ worker code exists but `arq` package not in dependencies
- `redis_url` config variable not defined
- Need to add Redis for async task queue

**Constraints:**
- Solo developer: prefer simple, well-maintained libraries
- Cost-effective: avoid paid APIs where free alternatives exist
- Async-first: heavy extraction should not block API response

## Goals / Non-Goals

**Goals:**
- MVP support for YouTube, Bilibili, Douyin, and generic web pages
- Full article text extraction for web pages
- Transcript extraction for video platforms
- Platform detection with appropriate icons
- Async processing for content extraction
- Reusable module for future inbox/studio integration

**Non-Goals:**
- Real-time video streaming or playback
- PDF generation from web pages
- Paid transcript services (Whisper, AssemblyAI)
- Screenshot/thumbnail generation from URLs (use platform OG images instead)

## Decisions

### 1. URL Extractor Module Structure

**Decision:** Create a dedicated `url_extractor` module under `infrastructure/` with a factory pattern for platform-specific handlers.

```
src/research_agent/infrastructure/url_extractor/
├── __init__.py
├── base.py              # Abstract base class, ExtractionResult dataclass
├── factory.py           # URLExtractorFactory - detects platform and returns handler
├── handlers/
│   ├── __init__.py
│   ├── youtube.py       # YouTube handler (transcript + metadata)
│   ├── bilibili.py      # Bilibili handler
│   ├── douyin.py        # Douyin handler
│   └── webpage.py       # Generic webpage handler (trafilatura)
└── utils.py             # URL parsing, platform detection utilities
```

**Rationale:** Factory pattern allows easy extension for new platforms. Consistent with existing `parser/` module structure.

### 2. Content Extraction Libraries

| Platform | Library | Rationale |
|----------|---------|-----------|
| Web Pages | `trafilatura` | Best-in-class article extraction, handles boilerplate removal, MIT license |
| YouTube | `youtube-transcript-api` | Free, no API key, supports auto-generated captions |
| Bilibili | `bilibili-api-python` | Community library, supports subtitle extraction |
| Douyin | `requests` + scraping | No stable API, minimal scraping for metadata |

**Alternatives Considered:**
- `newspaper3k`: Less maintained than trafilatura, more dependencies
- `yt-dlp`: Overkill for transcripts, designed for downloads
- Paid APIs (AssemblyAI): Cost prohibitive for solo project

### 3. Async Processing Flow

**Decision:** Follow the existing document processing pattern with ARQ.

```
User pastes URL → API validates URL → Create InboxItem (status=pending)
                                    → Enqueue ARQ task
                                    → Return immediately

ARQ Worker picks up task → Detect platform
                        → Extract content (title, text/transcript, thumbnail)
                        → Update InboxItem (status=ready, content filled)
                        → WebSocket notification (optional)
```

**Rationale:** Consistent with document upload flow. Users see immediate feedback while heavy extraction happens in background.

### 4. Data Model

**Decision:** Create a new `UrlContentModel` for persisting extracted URL content. This is a **standalone storage** that can be referenced by Inbox, Studio, or future features.

```python
# New model: url_contents table
class UrlContentModel(Base):
    __tablename__ = "url_contents"

    id: UUID                          # Primary key
    url: str                          # Original URL (unique index)
    platform: str                     # youtube, bilibili, douyin, web
    content_type: str                 # video, article, link
    
    # Extracted content
    title: str
    content: Optional[str]            # Article text or transcript
    thumbnail_url: Optional[str]
    
    # Platform-specific metadata
    meta_data: Dict[str, Any] = {
        "video_id": "dQw4w9WgXcQ",
        "channel_name": "Rick Astley",
        "duration": 212,              # seconds
    }
    
    # Processing status
    status: str = "pending"           # pending, processing, completed, failed
    error_message: Optional[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    extracted_at: Optional[datetime]  # When extraction completed
    
    # Optional: User ownership (for multi-tenant)
    user_id: Optional[str]
```

**Rationale:** 
- Separate from InboxItemModel - allows clean reuse by Studio, Inbox, or other features
- URL is indexed for deduplication (don't re-extract same URL)
- Inbox/Studio can create their own items and reference `url_content_id`

**Usage by consumers:**
```python
# Inbox creates item referencing extracted content
InboxItemModel(
    title=url_content.title,
    type=url_content.content_type,
    source_url=url_content.url,
    content=url_content.content,
    thumbnail_url=url_content.thumbnail_url,
    source_type="url_import",
    meta_data={"url_content_id": str(url_content.id), **url_content.meta_data},
)

# Studio can reference the same url_content for canvas nodes
```

### 5. Platform Detection

**Decision:** Use URL pattern matching with regex.

```python
PLATFORM_PATTERNS = {
    "youtube": [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
    ],
    "bilibili": [
        r"bilibili\.com/video/(BV[a-zA-Z0-9]+)",
        r"b23\.tv/([a-zA-Z0-9]+)",
    ],
    "douyin": [
        r"douyin\.com/video/(\d+)",
        r"v\.douyin\.com/([a-zA-Z0-9]+)",
    ],
}
```

**Fallback:** Any URL not matching known platforms is treated as a generic web page.

### 6. Icon Strategy

**Decision:** Pre-defined icons for known platforms, fallback to domain favicon.

| Platform | Icon | Color |
|----------|------|-------|
| YouTube | YouTube logo (Play button) | Red (#FF0000) |
| Bilibili | Bilibili logo (TV icon) | Blue (#00A1D6) |
| Douyin | Douyin logo (Music note) | Black (#000000) |
| Generic Web | Globe icon | Gray |

**Frontend Implementation:**
```typescript
// In InboxItemCard.tsx
const platformIcons: Record<string, { icon: IconType; color: string }> = {
  youtube: { icon: YouTubeIcon, color: '#FF0000' },
  bilibili: { icon: BilibiliIcon, color: '#00A1D6' },
  douyin: { icon: DouyinIcon, color: '#000000' },
  web: { icon: GlobeIcon, color: '#6B7280' },
};
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| YouTube blocks requests | Use rotating user-agents, respect rate limits |
| Bilibili API changes | Pin library version, add fallback to basic metadata |
| Douyin anti-scraping | Graceful degradation to title-only extraction |
| Large articles slow extraction | Set timeout (60s), truncate content if needed |
| Network failures | Retry with exponential backoff in ARQ task |

### Additional Challenges Identified

#### Video/Media Storage
| Issue | Decision |
|-------|----------|
| Video files | **NOT stored** - only metadata + transcript (Non-Goal) |
| Thumbnail URLs | **Store externally for MVP**, consider local copy later if URLs expire |
| Audio/playback | **NOT supported** - text content only |

#### Web Extraction Limitations
| Limitation | Handling |
|------------|----------|
| JavaScript-rendered (SPA) | Document as unsupported; return partial metadata |
| Paywalled content | Graceful degradation, extract public metadata only |
| Login-required pages | Mark as failed, return title from URL |
| Very large pages (>5MB) | Skip with error message |

#### Task Timeout Configuration
```python
# URL extraction should be fast - set dedicated timeout
URL_EXTRACTION_TIMEOUT = 60  # seconds (not 30 minutes like document processing)
```

#### China Platform Reality
| Platform | Subtitle Availability | Notes |
|----------|----------------------|-------|
| YouTube | ✅ Auto-generated common | Most videos have captions |
| Bilibili | ⚠️ Manual only (rare) | Most videos have NO subtitles |
| Douyin | ❌ Almost never | Short videos, no captions |

**MVP Scope Adjustment:**
- For Bilibili/Douyin without subtitles: Extract **video description** as content instead
- Mark `meta_data.has_transcript = false` when no subtitles available

#### URL Normalization Strategy
```python
# Normalize URLs before deduplication check
def normalize_url(url: str) -> str:
    # Remove tracking params: utm_*, fbclid, etc.
    # Normalize youtube.com variants
    # Keep essential params only (video ID, etc.)
```

#### Content Freshness
- **MVP**: No auto-refresh. Use `force: true` to re-extract.
- **Future**: Add `expires_at` field, re-extract after 30 days

## Migration Plan

1. **Database migration**: Create `url_contents` table with Alembic
2. Add new dependencies to `pyproject.toml`
3. Create URL extractor module
4. Add `UrlContentModel` to database models
5. Add ARQ task for URL processing
6. Add API endpoint `/api/v1/url/extract`
7. Wire up frontend ImportSourceDialog
8. Add platform icons utility

**Rollback:** Drop `url_contents` table if needed (no FK dependencies initially).

## Open Questions

1. **Transcript language preference:** Should we auto-detect or allow user to specify?
   - *Proposed:* Auto-detect with English fallback for MVP
   
2. **Content length limits:** Should we truncate very long articles/transcripts?
   - *Proposed:* Yes, 50,000 characters max for MVP (can be increased later)

3. **Retry policy:** How many times should we retry failed extractions?
   - *Proposed:* 3 retries with exponential backoff (1s, 2s, 4s)

