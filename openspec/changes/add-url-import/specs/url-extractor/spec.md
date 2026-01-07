# url-extractor Specification

## Purpose
A standalone, reusable backend module for extracting content from URLs. Supports multiple platforms (YouTube, Bilibili, Douyin, generic web pages) with a factory pattern for extensibility. Designed to be consumed by Inbox, Studio (Import Source), and future features.

## ADDED Requirements

### Requirement: URL Platform Detection
The URL extractor SHALL detect the content platform from a given URL and route to the appropriate extraction handler.

#### Scenario: Detect YouTube URL
- **WHEN** a URL matching `youtube.com/watch?v=*`, `youtu.be/*`, or `youtube.com/shorts/*` is provided
- **THEN** the system SHALL identify platform as "youtube"
- **AND** extract the video ID from the URL

#### Scenario: Detect Bilibili URL
- **WHEN** a URL matching `bilibili.com/video/BV*` or `b23.tv/*` is provided
- **THEN** the system SHALL identify platform as "bilibili"
- **AND** extract the video ID (BV number)

#### Scenario: Detect Douyin URL
- **WHEN** a URL matching `douyin.com/video/*` or `v.douyin.com/*` is provided
- **THEN** the system SHALL identify platform as "douyin"
- **AND** extract the video ID

#### Scenario: Fallback to generic web page
- **WHEN** a URL does not match any known platform pattern
- **THEN** the system SHALL treat it as a generic web page
- **AND** platform SHALL be set to "web"

### Requirement: Web Page Content Extraction
The URL extractor SHALL extract article content from generic web pages.

#### Scenario: Extract article content
- **WHEN** extracting content from a web page URL
- **THEN** the system SHALL extract:
  - Title (from meta tags or h1)
  - Main article text (boilerplate removed)
  - Thumbnail URL (from og:image or first significant image)
  - Site name (from og:site_name or domain)
- **AND** content SHALL be cleaned of HTML tags and navigation elements

#### Scenario: Handle non-article pages
- **WHEN** a web page has no discernible article content
- **THEN** the system SHALL extract available metadata (title, description, thumbnail)
- **AND** content MAY be empty or contain page description

### Requirement: YouTube Transcript Extraction
The URL extractor SHALL extract transcripts from YouTube videos.

#### Scenario: Extract auto-generated transcript
- **WHEN** extracting content from a YouTube video URL
- **THEN** the system SHALL extract:
  - Video title
  - Channel name
  - Thumbnail URL (maxresdefault or hqdefault)
  - Duration in seconds
  - Transcript text (auto-generated or manual captions)
- **AND** transcript SHALL be joined into readable paragraphs

#### Scenario: Handle videos without transcripts
- **WHEN** a YouTube video has no available transcripts
- **THEN** the system SHALL still extract video metadata
- **AND** content SHALL be empty with a note in `meta_data.extraction_error`

### Requirement: Bilibili Content Extraction
The URL extractor SHALL extract content from Bilibili videos.

#### Scenario: Extract Bilibili video info
- **WHEN** extracting content from a Bilibili video URL
- **THEN** the system SHALL extract:
  - Video title
  - Uploader name
  - Thumbnail URL
  - Duration in seconds
  - Subtitles/transcript if available
- **AND** if no subtitles available, use **video description** as content
- **AND** set `meta_data.has_transcript = false`

#### Scenario: Handle Bilibili API failures
- **WHEN** the Bilibili API is unavailable or rate-limited
- **THEN** the system SHALL fallback to basic metadata from page HTML
- **AND** log the error for debugging

### Requirement: Douyin Content Extraction
The URL extractor SHALL extract content from Douyin videos.

#### Scenario: Extract Douyin video info
- **WHEN** extracting content from a Douyin video URL
- **THEN** the system SHALL extract:
  - Video title/description (used as content since transcripts not available)
  - Creator name
  - Thumbnail URL (video cover)
- **AND** set `meta_data.has_transcript = false`

#### Scenario: Handle Douyin anti-scraping
- **WHEN** Douyin blocks the extraction request
- **THEN** the system SHALL return partial metadata
- **AND** set `meta_data.extraction_error` with failure reason

### Requirement: Extraction Result Format
The URL extractor SHALL return results in a consistent format across all platforms.

#### Scenario: Successful extraction result
- **WHEN** content extraction succeeds
- **THEN** the result SHALL include:
  - `title`: string
  - `content`: string (article text or transcript)
  - `thumbnail_url`: string or null
  - `platform`: "youtube" | "bilibili" | "douyin" | "web"
  - `content_type`: "video" | "article" | "link"
  - `metadata`: dict with platform-specific fields
  - `success`: true
  - `error`: null

#### Scenario: Failed extraction result
- **WHEN** content extraction fails
- **THEN** the result SHALL include:
  - `success`: false
  - `error`: string describing the failure
  - `title`: best-effort title or URL
  - Other fields MAY be null or partial

### Requirement: URL Content Persistence
The system SHALL persist extracted URL content to a database for reuse by consumers (Inbox, Studio, etc.).

#### Scenario: Store extracted content
- **WHEN** URL extraction completes successfully
- **THEN** the system SHALL create or update a `UrlContent` record with:
  - `url`: the original URL (unique constraint)
  - `platform`: detected platform
  - `content_type`: video, article, or link
  - `title`: extracted title
  - `content`: full text or transcript
  - `thumbnail_url`: preview image
  - `meta_data`: platform-specific fields
  - `status`: "completed"
  - `extracted_at`: current timestamp

#### Scenario: Avoid duplicate extraction
- **WHEN** a URL that has already been extracted is requested
- **THEN** the system SHALL return the existing `UrlContent` record
- **AND** skip re-extraction unless explicitly requested

#### Scenario: Handle extraction failure
- **WHEN** URL extraction fails
- **THEN** the system SHALL update `UrlContent` with:
  - `status`: "failed"
  - `error_message`: description of the failure
- **AND** partial data (title, etc.) SHALL be preserved if available

### Requirement: URL Extract API Endpoint
The system SHALL provide a generic API endpoint for extracting content from URLs.

#### Scenario: Extract and persist (default)
- **WHEN** a client sends a POST request to `/api/v1/url/extract` with:
  - `url`: valid HTTP/HTTPS URL
- **THEN** the system SHALL:
  - Validate the URL format
  - Check if URL already extracted (return cached if exists)
  - Create `UrlContent` record with status="pending"
  - Enqueue ARQ task for background extraction
  - Return the `UrlContent` record immediately
- **AND** the response status SHALL be 202 (Accepted)

#### Scenario: Force re-extraction
- **WHEN** a client sends a POST request with `force: true`
- **THEN** the system SHALL re-extract content even if cached
- **AND** update the existing `UrlContent` record

#### Scenario: Get extraction status
- **WHEN** a client sends a GET request to `/api/v1/url/extract/{id}`
- **THEN** the system SHALL return the `UrlContent` record
- **AND** include current `status` (pending, processing, completed, failed)

#### Scenario: Invalid URL format
- **WHEN** the provided URL is malformed or uses unsupported protocol
- **THEN** the system SHALL return 422 (Unprocessable Entity)
- **AND** include error message explaining the issue

