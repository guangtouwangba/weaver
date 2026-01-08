## ADDED Requirements

### Requirement: Universal Collection API Schema
The Collection API SHALL accept a standardized payload schema that supports multiple content types with platform-specific metadata for various integration sources.

#### Scenario: Collect web article via Chrome Extension
- **WHEN** a Chrome Extension sends a POST request to `/api/v1/inbox/collect` with:
  - `type`: "article"
  - `title`: "Competitor Analysis: Acme Corp launches new collaboration features"
  - `source_url`: "https://techblog.com/acme-corp-collab"
  - `content`: extracted article text
  - `thumbnail_url`: article preview image URL
  - `source_type`: "chrome_extension"
  - `tags`: ["Strategy", "Q1"]
  - `metadata`: { "author": "John Doe", "published_at": "2026-01-08" }
- **THEN** a new inbox item is created with all provided fields
- **AND** the response returns status 201 with the created item including its ID

#### Scenario: Collect quick note via Apple Shortcuts
- **WHEN** an iOS Shortcut sends a POST request to `/api/v1/inbox/collect` with:
  - `type`: "note"
  - `title`: "Idea: Mobile App Onboarding"
  - `content`: "Consider gamification elements for the first-time user experience..."
  - `source_type`: "ios_shortcut"
  - `tags`: ["Product", "UX"]
- **THEN** a new inbox item is created
- **AND** the `source_type` is recorded as "ios_shortcut" for analytics

### Requirement: Inbox Item Update Endpoint
The system SHALL allow partial updates to inbox items via PATCH requests.

#### Scenario: Mark item as read
- **WHEN** a PATCH request is sent to `/api/v1/inbox/items/{id}` with `{ "is_read": true }`
- **THEN** the item's `is_read` field is updated to true
- **AND** the new item counter decrements

#### Scenario: Add tags to item
- **WHEN** a PATCH request is sent to `/api/v1/inbox/items/{id}` with `{ "tag_ids": ["uuid1", "uuid2"] }`
- **THEN** the item's tags are replaced with the specified tags
- **AND** the updated item is returned with populated tag details

### Requirement: Collection Rate Limiting
The Collection API SHALL implement rate limiting to prevent abuse.

#### Scenario: Rate limit exceeded
- **WHEN** an API key makes more than 100 requests per minute
- **THEN** subsequent requests receive 429 Too Many Requests
- **AND** the response includes a `Retry-After` header indicating when requests can resume

#### Scenario: Batch collection efficiency
- **WHEN** a client needs to collect multiple items
- **THEN** they SHOULD use the batch endpoint `/api/v1/inbox/collect/batch`
- **AND** batch requests count as 1 request for rate limiting purposes

### Requirement: Content Preview Rendering
The Inbox preview panel SHALL render content-appropriate previews based on item type.

#### Scenario: Article preview
- **WHEN** a web article item is selected
- **THEN** the preview panel displays:
  - "Article" type badge with collection source
  - Article title as heading
  - Source URL as clickable link with external icon
  - Content preview area with skeleton loading placeholders
  - "Read Full Article" button

#### Scenario: Video preview
- **WHEN** a video item from YouTube is selected
- **THEN** the preview panel displays:
  - "Video" type badge with platform indicator
  - Video title as heading
  - Embedded video player or thumbnail with play button
  - Channel name and view count (if available)
  - Duration badge

#### Scenario: PDF preview
- **WHEN** a PDF item is selected
- **THEN** the preview panel displays:
  - "PDF Document" type badge
  - Document title
  - Thumbnail of first page (or placeholder)
  - Page count and file size (if available)

#### Scenario: Note preview
- **WHEN** a note item is selected
- **THEN** the preview panel displays:
  - "Note" type badge
  - Note title
  - Full note content in a readable format
  - Edit button to modify content

### Requirement: Manual Item Creation Dialog
The Inbox SHALL allow users to manually add new items via a dialog interface.

#### Scenario: Add URL manually
- **WHEN** a user clicks "+ New Item" button
- **AND** pastes a URL
- **THEN** the system extracts metadata from the URL (title, description, thumbnail)
- **AND** creates a new inbox item of appropriate type
- **AND** the item appears at the top of the inbox list

#### Scenario: Add quick note manually
- **WHEN** a user clicks "+ New Item" button
- **AND** selects "Quick Note"
- **AND** types note content
- **THEN** a new note item is created
- **AND** the item appears at the top of the inbox list

### Requirement: Project Assignment Workflow
The Inbox SHALL provide a streamlined workflow for assigning items to projects.

#### Scenario: Add to existing project via dropdown
- **WHEN** a user has an item selected
- **AND** opens the project dropdown in the action footer
- **THEN** they see a searchable list of all projects
- **WHEN** they select a project and click "Add"
- **THEN** the item is added to that project
- **AND** the item is removed from the inbox
- **AND** the next item is auto-selected

#### Scenario: Create new project and add item
- **WHEN** a user clicks "Create New Project"
- **AND** enters a project name
- **AND** confirms creation
- **THEN** a new project is created
- **AND** the current item is automatically added to the new project
- **AND** the user is optionally navigated to the new project's studio

### Requirement: WebSocket Collection Notifications
The system SHALL notify connected clients in real-time when new items are collected.

#### Scenario: Real-time inbox update
- **WHEN** a new item is collected via the API
- **AND** a user has the Inbox page open in their browser
- **THEN** the new item appears at the top of the list without page refresh
- **AND** the new item counter increments
- **AND** a subtle animation indicates the new arrival

## MODIFIED Requirements

### Requirement: Collection API Endpoint
The system SHALL provide a universal collection API endpoint for external clients (Chrome extension, mobile app, iOS Shortcuts, etc.) to submit content to the inbox.

#### Scenario: Collect web page via API
- **WHEN** an external client sends a POST request to `/api/v1/inbox/collect` with:
  - `type`: "article" | "video" | "link" | "note" | "pdf"
  - `title`: string
  - `source_url`: string (optional for notes)
  - `content`: string (extracted text or note body)
  - `thumbnail_url`: string (optional)
  - `source_type`: "chrome_extension" | "ios_shortcut" | "mobile_app" | "api" | "manual"
  - `tags`: string[] (optional, tag names or IDs)
  - `metadata`: object (optional, platform-specific data)
- **THEN** a new inbox item is created
- **AND** the response returns the created item with its ID
- **AND** the item appears in the user's inbox
- **AND** connected clients receive a WebSocket notification

#### Scenario: Authentication for collection API
- **WHEN** an external client calls the collection API
- **THEN** the request MUST include a valid API key in the `X-API-Key` header
- **AND** the item is associated with the API key's owner
- **AND** the API key's `last_used_at` timestamp is updated

#### Scenario: Collect video with platform metadata
- **WHEN** a video is collected from YouTube, Douyin, or Bilibili
- **THEN** the metadata field SHALL contain:
  - `platform`: "youtube" | "douyin" | "bilibili" | "vimeo"
  - `video_id`: string
  - `duration`: number (seconds, optional)
  - `channel_name`: string (optional)
  - `channel_avatar`: string URL (optional)
  - `view_count`: string (optional, e.g., "1.2M views")
  - `published_at`: string (optional, ISO date or relative)

#### Scenario: Invalid request handling
- **WHEN** a collection request has invalid or missing required fields
- **THEN** the response returns 422 Unprocessable Entity
- **AND** the response body includes field-specific validation errors

### Requirement: API Key Management
The system SHALL allow users to generate and manage API keys for external collection clients with detailed tracking.

#### Scenario: Generate API key
- **WHEN** a user navigates to Settings > API Keys
- **AND** clicks "Generate API Key"
- **AND** enters a name "Chrome Extension"
- **THEN** a new API key is created and displayed once
- **AND** the user can copy the key to clipboard
- **AND** the key is never shown again after navigating away

#### Scenario: List API keys
- **WHEN** a user views the API Keys section in settings
- **THEN** all existing keys are listed showing:
  - Key name
  - Creation date
  - Last used date (or "Never used")
  - Revoke button

#### Scenario: Revoke API key
- **WHEN** a user clicks "Revoke" on an API key
- **AND** confirms the action
- **THEN** the key is immediately invalidated
- **AND** any subsequent requests using that key receive 401 Unauthorized
- **AND** the key is removed from the user's key list
