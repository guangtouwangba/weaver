# inbox Specification

## Purpose
The Inbox is a specialized interface for collecting, previewing, and triaging content from various sources before assigning them to research projects.

## ADDED Requirements

### Requirement: Inbox Page Layout
The Inbox page SHALL display a two-column layout with a collected items list on the left and a preview panel on the right.

#### Scenario: Default layout structure
- **WHEN** a user navigates to the Inbox page
- **THEN** the left panel displays the "COLLECTED ITEMS" header with a new item counter badge
- **AND** a search bar and filter controls appear below the header
- **AND** the right panel shows a preview area for selected items
- **AND** project assignment controls appear at the bottom of the preview panel

### Requirement: Inbox Item Card Display
The Inbox SHALL display collected items as rich cards showing thumbnail, type, title, timestamp, and tags.

#### Scenario: Web article item card
- **WHEN** a web article is collected
- **THEN** the item card displays:
  - A colored icon indicating "Article" type (blue rectangle with document icon)
  - The article title as the main text
  - "Added [relative time] • Web Article" as metadata
  - Associated tags as colored chips below the metadata

#### Scenario: Video item card
- **WHEN** a video is collected from platforms like YouTube or Douyin
- **THEN** the item card displays:
  - A platform-specific icon (e.g., red play button for YouTube)
  - The video title as the main text
  - "Added [relative time] • Video" as metadata
  - Associated tags as colored chips

#### Scenario: PDF document item card
- **WHEN** a PDF document is collected
- **THEN** the item card displays:
  - A PDF icon (purple/pink document)
  - The filename as the main text
  - "Added [relative time] • PDF Document" as metadata
  - Associated tags if any

#### Scenario: Note item card
- **WHEN** a note is captured
- **THEN** the item card displays:
  - A note icon (orange/yellow lightbulb or sticky note)
  - The note title or first line as the main text
  - "Added [relative time] • Note" as metadata
  - Associated tags if any

### Requirement: Item Collection Source
The Inbox SHALL track and display the source of collected items.

#### Scenario: Display collection source
- **WHEN** an item is selected for preview
- **THEN** the preview panel header shows the collection source
- **AND** displays format like "Collected via Web Extension" or "Manually Added"

### Requirement: Tag System
The Inbox SHALL support tagging items for categorization.

#### Scenario: Display item tags
- **WHEN** an item has associated tags
- **THEN** the tags appear as colored chips on the item card
- **AND** each tag has a distinct color (e.g., Strategy=blue, Finance=red, Product=gray, UX=black)

#### Scenario: Filter by tag
- **WHEN** a user clicks the "Filter by Type/Tag" control
- **THEN** a dropdown appears showing available types and tags
- **WHEN** a tag filter is selected
- **THEN** only items with that tag are displayed in the list

### Requirement: Inbox Search
The Inbox SHALL provide search functionality to find collected items.

#### Scenario: Search items
- **WHEN** a user types in the search bar
- **THEN** the item list filters to show only items matching the search query
- **AND** the search matches against title, content, and tags

### Requirement: Item Preview Panel
The Inbox SHALL display a detailed preview of the selected item.

#### Scenario: Article preview
- **WHEN** a web article item is selected
- **THEN** the preview panel displays:
  - An "Article" type badge with source indicator
  - The article title as a heading
  - The source URL as a clickable link
  - A content preview area with extracted text
  - A "Read Full Article" button linking to the original source

#### Scenario: New item indicator
- **WHEN** an item is selected that was recently collected
- **THEN** a blue indicator dot appears on the item card in the list

### Requirement: Project Assignment
The Inbox SHALL allow users to assign items to existing projects or create new projects.

#### Scenario: Add to existing project
- **WHEN** an item is selected
- **THEN** the preview panel shows "Add to Existing Project" section
- **AND** a dropdown lists available projects
- **WHEN** a user selects a project and clicks "Add"
- **THEN** the item is added to that project's resources
- **AND** the item is optionally removed from the inbox

#### Scenario: Create new project from item
- **WHEN** a user clicks "Create New Project" button
- **THEN** a new project is created with the item's title or a default name
- **AND** the item is added to the new project as the first resource
- **AND** the user is navigated to the new project's studio

### Requirement: New Item Counter
The Inbox header SHALL display a count of new/unread items.

#### Scenario: Display new item count
- **WHEN** there are unread items in the inbox
- **THEN** a badge displays the count (e.g., "12 New") next to the "COLLECTED ITEMS" header

#### Scenario: Mark items as read
- **WHEN** a user selects and previews an item
- **THEN** the item is marked as read
- **AND** the new item counter decrements

### Requirement: Add New Item
The Inbox SHALL provide a way to manually add new items.

#### Scenario: Add new item button
- **WHEN** a user clicks the "+ New Item" button in the header
- **THEN** a dialog or input appears to capture a new item
- **AND** the user can enter a URL, paste text, or type a note

### Requirement: Collection API Endpoint
The system SHALL provide a universal collection API endpoint for external clients (Chrome extension, mobile app, etc.) to submit content to the inbox.

#### Scenario: Collect web page via API
- **WHEN** an external client sends a POST request to `/api/inbox/collect` with:
  - `type`: "article" | "video" | "link" | "note" | "pdf"
  - `title`: string
  - `url`: string (optional for notes)
  - `content`: string (extracted text or note body)
  - `thumbnail_url`: string (optional)
  - `source_type`: "chrome_extension" | "mobile_app" | "api"
  - `tags`: string[] (optional)
  - `metadata`: object (optional, platform-specific data)
- **THEN** a new inbox item is created
- **AND** the response returns the created item with its ID
- **AND** the item appears in the user's inbox

#### Scenario: Authentication for collection API
- **WHEN** an external client calls the collection API
- **THEN** the request MUST include a valid API key or Bearer token
- **AND** the item is associated with the authenticated user

#### Scenario: Collect video with platform metadata
- **WHEN** a video is collected from YouTube or Douyin
- **THEN** the metadata field SHALL contain:
  - `platform`: "youtube" | "douyin" | "bilibili" | etc.
  - `video_id`: string
  - `duration`: number (seconds, optional)
  - `channel_name`: string (optional)

### Requirement: API Key Management
The system SHALL allow users to generate and manage API keys for external collection clients.

#### Scenario: Generate API key
- **WHEN** a user navigates to settings and clicks "Generate API Key"
- **THEN** a new API key is created and displayed once
- **AND** the key can be named for identification (e.g., "Chrome Extension")

#### Scenario: Revoke API key
- **WHEN** a user revokes an API key
- **THEN** any subsequent requests using that key are rejected
- **AND** the key is removed from the user's key list

### Requirement: Batch Collection
The system SHALL support collecting multiple items in a single API request.

#### Scenario: Batch collect items
- **WHEN** an external client sends a POST request to `/api/inbox/collect/batch` with an array of items
- **THEN** all valid items are created
- **AND** the response includes success/failure status for each item
- **AND** partial failures do not prevent successful items from being created
