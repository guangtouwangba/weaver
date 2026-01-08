# Tasks: Add Universal Inbox Collection API

## 1. Backend API Enhancements

- [ ] 1.1 Add comprehensive request validation with Pydantic for collection endpoints
- [ ] 1.2 Implement `PATCH /api/v1/inbox/items/{id}` endpoint for partial updates
- [ ] 1.3 Add pagination with total count to list endpoint
- [ ] 1.4 Add rate limiting middleware for collection endpoints
- [ ] 1.5 Implement WebSocket notification for new item collection

## 2. API Key Management

- [ ] 2.1 Create `ApiKeyModel` database model with fields: id, user_id, name, key_hash, created_at, last_used_at
- [ ] 2.2 Implement API key generation endpoint `POST /api/v1/settings/api-keys`
- [ ] 2.3 Implement API key listing endpoint `GET /api/v1/settings/api-keys` (returns metadata, not keys)
- [ ] 2.4 Implement API key revocation endpoint `DELETE /api/v1/settings/api-keys/{id}`
- [ ] 2.5 Update API key authentication to track last_used_at

## 3. Frontend Inbox Enhancements

- [ ] 3.1 Implement item type icons per design (Article=blue, Video=red, PDF=purple, Note=orange, Link=gray)
- [ ] 3.2 Add skeleton loading state for preview panel
- [ ] 3.3 Implement content preview based on item type (article summary, video embed, PDF thumbnail)
- [ ] 3.4 Add "Read Full Article" button that opens source URL in new tab
- [ ] 3.5 Implement "New Item" dialog for manual URL/note capture

## 4. Settings Page - API Key Management UI

- [ ] 4.1 Create API Keys section in settings page
- [ ] 4.2 Implement "Generate API Key" button with name input
- [ ] 4.3 Display generated key once with copy button (never shown again)
- [ ] 4.4 List existing keys with name, creation date, last used date
- [ ] 4.5 Add revoke button with confirmation dialog

## 5. Project Assignment Workflow

- [ ] 5.1 Implement project dropdown with search in action footer
- [ ] 5.2 Add "Create New Project" button that opens project creation dialog
- [ ] 5.3 After creation, auto-select new project and add current item
- [ ] 5.4 After assignment, auto-advance to next unprocessed item
- [ ] 5.5 Show toast confirmation after successful assignment

## 6. Documentation

- [ ] 6.1 Create API documentation for collection endpoints
- [ ] 6.2 Write Chrome extension integration guide
- [ ] 6.3 Write Apple Shortcuts integration example

