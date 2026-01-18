## ADDED Requirements

### Requirement: Resource Domain Entity
The system SHALL provide a unified `Resource` domain entity that abstracts content from different source models.

#### Scenario: Document as Resource
- **WHEN** a `DocumentModel` is converted to a `Resource`
- **THEN** the `Resource` SHALL have:
  - `id`: Document UUID
  - `type`: `ResourceType.DOCUMENT`
  - `title`: Document original filename
  - `content`: Document full_content or summary
  - `metadata`: Parsing metadata, page count, OCR status
  - `metadata.platform`: "local"
  - `thumbnail_url`: Document thumbnail URL
  - `source_url`: null (local file)
  - `created_at` and `updated_at` from document

#### Scenario: Video as Resource (YouTube)
- **WHEN** a `UrlContentModel` with platform="youtube" is converted to a `Resource`
- **THEN** the `Resource` SHALL have:
  - `id`: UrlContent UUID
  - `type`: `ResourceType.VIDEO`
  - `title`: Video title
  - `content`: Video transcript (if available)
  - `metadata.platform`: "youtube"
  - `metadata.video_id`: Platform-specific video ID
  - `metadata.channel_name`: Channel or author name
  - `metadata.duration`: Video duration in seconds
  - `metadata.view_count`: View count (if available)
  - `thumbnail_url`: Video thumbnail URL
  - `source_url`: Original video URL
  - `created_at` and `updated_at` from url_content

#### Scenario: Video as Resource (Bilibili)
- **WHEN** a `UrlContentModel` with platform="bilibili" is converted to a `Resource`
- **THEN** the `Resource` SHALL have:
  - `id`: UrlContent UUID
  - `type`: `ResourceType.VIDEO`
  - `title`: Video title
  - `content`: Video transcript or subtitle (if available)
  - `metadata.platform`: "bilibili"
  - `metadata.video_id`: BV or AV number
  - Other fields same as YouTube scenario

#### Scenario: Video as Resource (local upload)
- **WHEN** a `DocumentModel` with mime_type="video/*" is converted to a `Resource`
- **THEN** the `Resource` SHALL have:
  - `id`: Document UUID
  - `type`: `ResourceType.VIDEO`
  - `title`: Original filename
  - `content`: Extracted transcript (if processed)
  - `metadata.platform`: "local"
  - `metadata.duration`: Video duration (if extracted)
  - `thumbnail_url`: Generated thumbnail (if available)
  - `source_url`: null (local file)

#### Scenario: Audio as Resource (local upload)
- **WHEN** a `DocumentModel` with mime_type="audio/*" is converted to a `Resource`
- **THEN** the `Resource` SHALL have:
  - `id`: Document UUID
  - `type`: `ResourceType.AUDIO`
  - `title`: Original filename
  - `content`: Extracted transcript (if processed via speech-to-text)
  - `metadata.platform`: "local"
  - `metadata.duration`: Audio duration (if extracted)
  - `thumbnail_url`: null or album art (if available)
  - `source_url`: null (local file)

#### Scenario: Audio as Resource (podcast URL)
- **WHEN** a `UrlContentModel` with content_type="audio" is converted to a `Resource`
- **THEN** the `Resource` SHALL have:
  - `id`: UrlContent UUID
  - `type`: `ResourceType.AUDIO`
  - `title`: Episode or audio title
  - `content`: Transcript (if available)
  - `metadata.platform`: Platform name (e.g., "spotify", "apple_podcasts", "web")
  - `thumbnail_url`: Podcast artwork URL
  - `source_url`: Original audio URL

#### Scenario: Web Page as Resource
- **WHEN** a `UrlContentModel` with content_type="article" or platform="web" is converted to a `Resource`
- **THEN** the `Resource` SHALL have:
  - `id`: UrlContent UUID
  - `type`: `ResourceType.WEB_PAGE`
  - `title`: Page title or URL
  - `content`: Extracted article text
  - `metadata.platform`: "web"
  - `thumbnail_url`: OG image or null
  - `source_url`: Original URL
  - `created_at` and `updated_at` from url_content

### Requirement: ResourceType Enumeration
The system SHALL define a comprehensive `ResourceType` enum based on content category, not platform or source.

#### Scenario: ResourceType values
- **WHEN** the `ResourceType` enum is defined
- **THEN** it SHALL include:
  - `DOCUMENT` for text documents (PDF, Word, PPT, Markdown, plain text)
  - `VIDEO` for video content (local files, YouTube, Bilibili, Douyin, etc.)
  - `AUDIO` for audio content (MP3, WAV, podcasts, etc.)
  - `WEB_PAGE` for web articles and generic web pages
  - `IMAGE` for images (PNG, JPG, diagrams, screenshots)
  - `NOTE` for user-created notes within the system
- **AND** platform/source SHALL be stored in `metadata.platform`:
  - "local" for uploaded files
  - "youtube", "bilibili", "douyin" for video platforms
  - "spotify", "apple_podcasts" for audio platforms
  - "web" for extracted web pages
  - "notion", "twitter", etc. for future integrations

#### Scenario: ResourceType extensibility
- **WHEN** a new content type needs to be added
- **THEN** only the `ResourceType` enum and a new adapter need modification
- **AND** existing Resource-consuming code SHALL work without changes

#### Scenario: New platform support
- **WHEN** a new platform for an existing content type needs support (e.g., TikTok for VIDEO)
- **THEN** only a new URL extractor handler needs implementation
- **AND** ResourceType remains unchanged
- **AND** all VIDEO consumers automatically support the new platform

### Requirement: Resource Resolver Service
The system SHALL provide a `ResourceResolver` service to convert resource IDs to unified `Resource` objects.

#### Scenario: Resolve single resource by ID
- **WHEN** `ResourceResolver.resolve(id)` is called with a valid UUID
- **THEN** the resolver SHALL:
  - Check `DocumentModel` for matching ID
  - Check `UrlContentModel` for matching ID
  - Return a `Resource` object if found
  - Return `None` if no match in any model

#### Scenario: Resolve with type hint
- **WHEN** `ResourceResolver.resolve(id, type_hint=ResourceType.VIDEO)` is called
- **THEN** the resolver SHALL query only video-capable sources
- **AND** return the result faster than querying all models

#### Scenario: Resolve with platform hint
- **WHEN** `ResourceResolver.resolve(id, platform_hint="youtube")` is called
- **THEN** the resolver SHALL query only `UrlContentModel` with platform="youtube"
- **AND** return the result faster than full scan

#### Scenario: Resolve multiple resources
- **WHEN** `ResourceResolver.resolve_many([id1, id2, id3])` is called
- **THEN** the resolver SHALL batch queries to minimize database round trips
- **AND** return resources in the same order as input IDs
- **AND** skip any IDs that don't resolve

#### Scenario: Get content shortcut
- **WHEN** `ResourceResolver.get_content(id)` is called
- **THEN** the resolver SHALL resolve the resource and return only the content string
- **AND** return empty string if resource not found or has no content

### Requirement: Generation Content Loading via ResourceResolver
The output generation service SHALL use `ResourceResolver` to load content from any resource type.

#### Scenario: Load content from mixed resource types
- **WHEN** output generation is requested with documents, videos, and audio resources
- **THEN** the service SHALL resolve all IDs through `ResourceResolver`
- **AND** combine content from all resolved resources
- **AND** proceed with generation using the combined content

#### Scenario: Backward compatible content loading
- **WHEN** output generation is requested with only `document_ids` (legacy format)
- **THEN** the service SHALL continue to work as before
- **AND** internally use `ResourceResolver` for content loading

#### Scenario: Content loading failure handling
- **WHEN** `ResourceResolver` fails to find a resource
- **THEN** the service SHALL log a warning
- **AND** continue with other resolved resources
- **AND** fail only if ALL resources fail to resolve

### Requirement: Chat Context via ResourceResolver
The chat streaming service SHALL use `ResourceResolver` to load context from any resource type.

#### Scenario: Mixed context sources
- **WHEN** a chat query includes context from multiple resource types
- **THEN** the service SHALL resolve all context IDs through `ResourceResolver`
- **AND** format content appropriately based on resource type
- **AND** include source attribution (document name, video title, URL)

#### Scenario: Video content in chat context
- **WHEN** a video resource is included as chat context
- **THEN** the system SHALL include the video title and transcript
- **AND** format as "## Video ({platform}): {title}\n{transcript}"
- **AND** the AI SHALL be able to answer questions about the video content

#### Scenario: Audio content in chat context
- **WHEN** an audio resource is included as chat context
- **THEN** the system SHALL include the audio title and transcript
- **AND** format as "## Audio ({platform}): {title}\n{transcript}"
- **AND** the AI SHALL be able to answer questions about the audio content

#### Scenario: Document content in chat context
- **WHEN** a document resource is included as chat context
- **THEN** the system SHALL include the document title and content
- **AND** format as "## Document: {title}\n{content}"
- **AND** the AI SHALL be able to answer questions about the document
