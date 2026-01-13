# Tasks: Fix User Data Isolation

## Phase 1: Core Infrastructure

1. [x] **Add `get_verified_project` dependency to `api/deps.py`**
   - Create function that verifies project ownership
   - Handle auth bypass for development mode
   - Return verified Project entity

## Phase 2: Apply to Endpoints

2. [x] **Fix `api/v1/chat.py`**
   - Add `get_verified_project` dependency to `stream_message`
   - Add `get_verified_project` dependency to `get_chat_history`
   - Add `get_optional_user` import

3. [x] **Fix `api/v1/outputs.py`**
   - Add `get_verified_project` dependency to all 8 endpoints
   - Add `get_optional_user` import

4. [x] **Fix `api/v1/url.py`**
   - Add `get_verified_project` dependency to `extract_url`
   - Add `get_verified_project` dependency to `list_project_url_contents`

5. [x] **Fix `api/v1/canvas.py`**
   - Add `get_verified_project` dependency to all 6 endpoints

6. [x] **Fix `api/v1/documents.py`**
   - Add `get_verified_project` dependency to `confirm_upload`

## Phase 3: Inbox User Scoping

7. [ ] **Add user scoping to `api/v1/inbox.py`**
   - Add `user_id` field to InboxItem model
   - Filter inbox queries by current user
   - Update collection endpoints to set user_id

## Phase 4: Verification

8. [ ] **Manual Testing**
   - Test with two different user accounts
   - Verify User A cannot see User B's:
     - Documents
     - Chat history
     - Outputs (mindmaps, summaries)
     - Canvas nodes
     - URL contents

9. [ ] **Add integration tests** (optional, if time permits)
   - Test 403 response for unauthorized project access
   - Test 404 response for non-existent project

## Dependencies

- Tasks 2-6 can be done in parallel
- Task 7 (Inbox) is independent and lower priority
- Task 8 requires all previous tasks complete

