# Fix User Data Isolation

## Problem Statement

User A can see User B's content due to missing user ownership verification in API endpoints. The `user_id` field exists in the Project entity and is correctly used in `projects.py`, but **most other endpoints do not verify project ownership** before allowing access to project-scoped resources.

### Root Cause Analysis

The application architecture relies on **project-level isolation**: resources (documents, outputs, chat, canvas nodes, URL contents) belong to projects, and projects belong to users. However:

1. **Inconsistent enforcement**: Only `projects.py` consistently verifies `project.user_id == current_user.user_id`
2. **Missing verification in multiple endpoints**:
   - `chat.py`: No user verification at all
   - `outputs.py`: No user verification at all
   - `url.py`: No user verification at all
   - `canvas.py`: No user verification at all
   - `documents.py`: `confirm_upload` endpoint missing verification
   - `inbox.py`: Uses API key auth but no user scoping

3. **Code pattern gap**: Endpoints accept `project_id` as a URL parameter but don't verify the project belongs to the authenticated user before proceeding

## Proposed Solution

Introduce a **centralized project ownership verification dependency** that:
1. Extracts `project_id` from the request path
2. Queries the project from the database
3. Verifies `project.user_id == current_user.user_id`
4. Returns 403 Forbidden if ownership check fails
5. Returns 404 if project doesn't exist

Then apply this dependency to all project-scoped endpoints.

## Affected Endpoints

| File | Endpoints | Current State | Action |
|------|-----------|---------------|--------|
| `chat.py` | `stream_message`, `get_chat_history` | ❌ No user check | Add verification |
| `outputs.py` | All 8 endpoints | ❌ No user check | Add verification |
| `url.py` | `extract_url`, `list_project_url_contents` | ❌ No user check | Add verification |
| `canvas.py` | All 6 endpoints | ❌ No user check | Add verification |
| `documents.py` | `confirm_upload` | ❌ No user check | Add verification |
| `documents.py` | Other endpoints | ✅ Has verification | Keep existing |
| `inbox.py` | All endpoints | ⚠️ API key only | Add user scoping |

## User Review Required

> [!IMPORTANT]
> This change will enforce authentication on previously unauthenticated endpoints.
> Users who previously accessed resources without proper authentication will be blocked.

> [!WARNING]  
> **Breaking Change**: Any external integrations accessing project resources without proper user authentication will fail with 403 Forbidden.

