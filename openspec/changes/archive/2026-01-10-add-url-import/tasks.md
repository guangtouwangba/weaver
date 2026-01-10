# Tasks: Add URL Import Capability

## 0. Prerequisites: ARQ + Redis Setup (Missing in Project)

- [x] 0.1 Add `arq` to `pyproject.toml` dependencies
- [x] 0.2 Add `redis_url: str = ""` to `config.py` Settings class
- [x] 0.3 Add `REDIS_URL` to `env.example` with documentation
- [x] 0.4 Update docker-compose.yml to include Redis service (for local dev)
- [ ] 0.5 Verify ARQ worker starts correctly with `make worker` *(requires running services)*

## 1. Backend: Database & Models

- [x] 1.1 Create Alembic migration for `url_contents` table
- [x] 1.2 Add `UrlContentModel` to `infrastructure/database/models.py`
- [x] 1.3 Create `UrlContentRepository` with CRUD operations
- [x] 1.4 Add unique index on `url` column for deduplication

## 2. Backend: URL Extractor Module (Core - Reusable)

- [x] 2.1 Add dependencies to `pyproject.toml`: `trafilatura`, `youtube-transcript-api`, `bilibili-api-python`
- [x] 2.2 Create `src/research_agent/infrastructure/url_extractor/` directory structure
- [x] 2.3 Implement `base.py` with `ExtractionResult` dataclass and `URLExtractor` abstract base class
- [x] 2.4 Implement `utils.py` with URL validation, platform detection, and URL normalization
- [x] 2.5 Implement `factory.py` with `URLExtractorFactory` that returns appropriate handler
- [x] 2.6 Implement `handlers/webpage.py` using trafilatura for article extraction
- [x] 2.7 Implement `handlers/youtube.py` using youtube-transcript-api
- [x] 2.8 Implement `handlers/bilibili.py` using bilibili-api-python
- [x] 2.9 Implement `handlers/douyin.py` with basic metadata extraction

## 3. Backend: ARQ Task & API

- [x] 3.1 Create `src/research_agent/worker/tasks/url_processor.py` with `URLProcessorTask`
- [x] 3.2 Register `process_url` function in `arq_config.py`
- [x] 3.3 Add `POST /api/v1/url/extract` endpoint with persistence
- [x] 3.4 Add `GET /api/v1/url/extract/{id}` endpoint for status polling
- [x] 3.5 Create `URLExtractRequest` and `URLExtractResponse` DTOs
- [x] 3.6 Implement deduplication logic (return cached if URL already extracted)

## 4. Frontend: ImportSourceDialog Integration

- [x] 4.1 Add `extractUrl` function to `lib/api.ts` calling new endpoint
- [x] 4.2 Add `getUrlContent` function for polling extraction status
- [x] 4.3 Wire up `onUrlImport` prop in Studio's ImportSourceDialog usage
- [x] 4.4 Show loading state while URL is being processed
- [x] 4.5 Poll for completion and display result
- [x] 4.6 Display error toast if URL extraction fails

## 5. Frontend: Platform Icons

- [x] 5.1 Add YouTube, Bilibili, Douyin SVG icons to `components/ui/icons/`
- [x] 5.2 Create `getPlatformIcon()` utility function for consistent icon rendering
- [x] 5.3 Fallback to generic Globe icon for unknown platforms

## 6. Validation & Testing

- [x] 6.1 Unit test URL platform detection with various URL formats (25 tests passing)
- [ ] 6.2 Unit test each extraction handler with mocked responses *(deferred - requires mocking external APIs)*
- [ ] 6.3 Integration test: extract YouTube URL, verify persistence *(requires running services)*
- [ ] 6.4 Integration test: extract web article, verify content stored *(requires running services)*
- [ ] 6.5 Integration test: deduplication (same URL returns cached) *(requires running services)*
- [ ] 6.6 Manual test: end-to-end flow in browser *(requires running services)*

---

> **Note:** Inbox-specific integration (InboxItemCard icons, inbox item creation) will be handled separately. The URL Extractor module is designed to be reusable by both Inbox and Studio (Import Source).
