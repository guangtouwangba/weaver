# Change: Integrate Supabase Authentication with User Resource Isolation

## Why
The application currently operates without user authentication, using a hardcoded `DEFAULT_USER_ID` placeholder. To support multi-user deployment and protect user data, we need to integrate Supabase Auth for authentication and scope all resources (projects, documents, files) by user.

## What Changes

### Frontend
- Add Supabase Auth UI components for login/signup/logout
- Implement auth state management with session persistence
- Add JWT token to all API requests via Authorization header
- Create protected routes that redirect to login when unauthenticated
- Support anonymous trial mode with conversion to authenticated user

### Backend
- Add Supabase JWT verification middleware
- Add `user_id` column to `projects` table (foreign key concept, not enforced)
- Update all project queries to filter by authenticated user
- Update file storage paths to include user ID prefix: `{user_id}/{project_id}/{filename}`
- Create database migration for schema changes

### Configuration
- Add Supabase Auth environment variables (`SUPABASE_JWT_SECRET`, `SUPABASE_ANON_KEY`)
- Update CORS to allow Supabase Auth origins

## Impact
- **Breaking**: Database schema change requires migration (clean slate approach)
- Affected specs: New `auth` capability
- Affected code:
  - `app/frontend/src/lib/api.ts` - Add auth headers
  - `app/frontend/src/app/*` - Protected routes
  - `app/backend/src/research_agent/api/*` - Auth middleware
  - `app/backend/src/research_agent/infrastructure/database/models.py` - Add user_id
  - `app/backend/src/research_agent/infrastructure/storage/*` - User-scoped paths
