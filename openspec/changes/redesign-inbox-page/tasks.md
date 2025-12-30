# Tasks: Redesign Inbox Page

## 1. Database & API Foundation
- [ ] 1.1 Create `inbox_items` table schema (id, title, type, source_url, content, thumbnail_url, source_type, metadata, collected_at, is_read, user_id)
- [ ] 1.2 Create `inbox_item_tags` junction table for item-tag relationships
- [ ] 1.3 Create `tags` table if not exists (id, name, color, user_id)
- [ ] 1.4 Create `api_keys` table (id, name, key_hash, user_id, created_at, last_used_at, revoked_at)
- [ ] 1.5 Create CRUD API endpoints for inbox items (`/api/inbox/`)
- [ ] 1.6 Create API endpoint for tag management (`/api/tags/`)
- [ ] 1.7 Create API endpoint for project assignment (`/api/inbox/{id}/assign`)

## 2. Collection API (For Chrome Extension)
- [ ] 2.1 Create `POST /api/inbox/collect` endpoint for single item collection
- [ ] 2.2 Create `POST /api/inbox/collect/batch` endpoint for batch collection
- [ ] 2.3 Implement API key authentication middleware
- [ ] 2.4 Create API key management endpoints (`/api/settings/api-keys/`)
- [ ] 2.5 Add request validation for collection payload (type, title, url, content, metadata)
- [ ] 2.6 Handle platform-specific metadata (YouTube, Douyin, Bilibili)

## 3. Frontend Components
- [ ] 3.1 Create `InboxItemCard` component with thumbnail, type icon, title, tags, timestamp
- [ ] 3.2 Create `InboxItemList` component with scrollable list layout
- [ ] 3.3 Create `InboxSearchBar` component with search input
- [ ] 3.4 Create `InboxFilterDropdown` component for type/tag filtering
- [ ] 3.5 Create `InboxPreviewPanel` component for content preview
- [ ] 3.6 Create `ProjectAssignmentPanel` component with dropdown and "Create New" button
- [ ] 3.7 Create `TagChip` component with colored badges

## 4. Page Integration
- [ ] 4.1 Redesign `/inbox` page layout with left list panel and right preview panel
- [ ] 4.2 Integrate search and filter controls in header area
- [ ] 4.3 Implement item selection state and preview rendering
- [ ] 4.4 Implement "Add to Project" workflow
- [ ] 4.5 Implement "Create New Project" from inbox item flow
- [ ] 4.6 Add new item counter badge in header

## 5. Settings: API Key Management
- [ ] 5.1 Add API Keys section to settings page
- [ ] 5.2 Implement "Generate API Key" UI with name input
- [ ] 5.3 Implement key list with revoke action
- [ ] 5.4 Show one-time key display modal after generation

## 6. Verification
- [ ] 6.1 Write API integration tests for inbox CRUD operations
- [ ] 6.2 Write API tests for collection endpoint with valid/invalid payloads
- [ ] 6.3 Write API tests for API key authentication
- [ ] 6.4 Write component tests for InboxItemCard
- [ ] 6.5 Manual testing: test collection API with curl/Postman
- [ ] 6.6 Manual testing: assign items to projects and verify project content
