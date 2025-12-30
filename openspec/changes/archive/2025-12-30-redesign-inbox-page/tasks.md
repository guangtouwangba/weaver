# Tasks: Redesign Inbox Page

## 1. Database & API Foundation
- [x] 1.1 Create `inbox_items` table schema (id, title, type, source_url, content, thumbnail_url, source_type, metadata, collected_at, is_read, user_id)
- [x] 1.2 Create `inbox_item_tags` junction table for item-tag relationships
- [x] 1.3 Create `tags` table if not exists (id, name, color, user_id)
- [x] 1.4 Create `api_keys` table (id, name, key_hash, user_id, created_at, last_used_at, revoked_at)
- [x] 1.5 Create CRUD API endpoints for inbox items (`/api/inbox/`)
- [x] 1.6 Create API endpoint for tag management (`/api/tags/`)
- [x] 1.7 Create API endpoint for project assignment (`/api/inbox/{id}/assign`)

## 2. Collection API (For Chrome Extension)
- [x] 2.1 Create `POST /api/inbox/collect` endpoint for single item collection
- [x] 2.2 Create `POST /api/inbox/collect/batch` endpoint for batch collection
- [x] 2.3 Implement API key authentication middleware
- [x] 2.4 Create API key management endpoints (`/api/settings/api-keys/`)
- [x] 2.5 Add request validation for collection payload (type, title, url, content, metadata)
- [x] 2.6 Handle platform-specific metadata (YouTube, Douyin, Bilibili)

## 3. Frontend Components (Design Aligned)
- [x] 3.1 Create `InboxHeader` component with "Inbox" title, Search Bar, Filter button, "New Item" button, and Notification bell
- [x] 3.2 Create `InboxSidebar` component with "COLLECTED ITEMS" header, count badge, and list virtualization
- [x] 3.3 Create `InboxItemCard` component matching design: icon container, title, metadata row ("Added today • Type"), and tags row
- [x] 3.4 Create `InboxPreviewHeader` component: Type badge, "Collected via...", Edit/Delete icons
- [x] 3.5 Create `InboxContentPreview` component: Skeleton loading state, content placeholder, "Read Full Article" button
- [x] 3.6 Create `InboxActionFooter` component: Split section for "Add to Existing Project" (Dropdown + Add) and "Start Fresh" (Create New Project button)
- [x] 3.7 Create `TagChip` component with specific color variants (purple for Product, blue for Strategy, green for Finance/Market)

## 4. Page Integration
- [x] 4.1 Implement `InboxPage` layout: Fixed header, scrollable sidebar (left), scrollable preview (right)
- [x] 4.2 wire up `InboxHeader` search and filter to URL state or local state
- [x] 4.3 Implement item selection logic with active state styling (blue background/border)
- [x] 4.4 Implement "Add to Project" API integration in `InboxActionFooter`
- [x] 4.5 Implement "Create New Project" modal flow
- [x] 4.6 Implement "Delete Item" confirmation flow
- [x] 4.7 Implement "Edit Item" modal (title, tags, content)

## 5. Settings: API Key Management
- [x] 5.1 Add API Keys section to settings page
- [x] 5.2 Implement "Generate API Key" UI with name input
- [x] 5.3 Implement key list with revoke action
- [x] 5.4 Show one-time key display modal after generation

## 6. Verification
- [ ] 6.1 Write API integration tests for inbox CRUD operations
- [ ] 6.2 Write API tests for collection endpoint with valid/invalid payloads
- [ ] 6.3 Write API tests for API key authentication
- [ ] 6.4 Write component tests for InboxItemCard
- [ ] 6.5 Manual testing: test collection API with curl/Postman
- [ ] 6.6 Manual testing: assign items to projects and verify project content
