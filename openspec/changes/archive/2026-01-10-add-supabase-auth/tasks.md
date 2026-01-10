# Tasks: Add Supabase Authentication

## 1. Backend Authentication Infrastructure
- [ ] 1.1 Add `supabase` Python package to dependencies
- [ ] 1.2 Add auth environment variables to `config.py` (`SUPABASE_JWT_SECRET`, `SUPABASE_ANON_KEY`)
- [ ] 1.3 Create JWT verification utility in `api/auth/supabase.py`
- [ ] 1.4 Create `get_current_user` FastAPI dependency that extracts user_id from JWT
- [ ] 1.5 Create `get_optional_user` dependency for anonymous-allowed endpoints
- [ ] 1.6 Add unit tests for JWT verification

## 2. Database Schema Update
- [ ] 2.1 Add `user_id` column to `ProjectModel` in `models.py`
- [ ] 2.2 Create Alembic migration for `user_id` column
- [ ] 2.3 Update `ProjectRepository` to accept and filter by `user_id`
- [ ] 2.4 Update project API endpoints to use authenticated user context

## 3. User-Scoped Project Access
- [ ] 3.1 Update `POST /api/v1/projects` to set `user_id` from auth context
- [ ] 3.2 Update `GET /api/v1/projects` to filter by authenticated user
- [ ] 3.3 Update `GET /api/v1/projects/{id}` to verify user ownership
- [ ] 3.4 Update `DELETE /api/v1/projects/{id}` to verify user ownership
- [ ] 3.5 Add 403 Forbidden responses for unauthorized access attempts

## 4. User-Scoped File Storage
- [ ] 4.1 Update local storage path to include `user_id` prefix
- [ ] 4.2 Update Supabase Storage paths to include `user_id` prefix
- [ ] 4.3 Update file download/serve endpoints to verify user ownership
- [ ] 4.4 Update document upload flow to use user-scoped paths

## 5. Frontend Auth UI Setup
- [ ] 5.1 Install `@supabase/supabase-js` and `@supabase/auth-ui-react` packages
- [ ] 5.2 Create Supabase client configuration in `lib/supabase.ts`
- [ ] 5.3 Create `AuthProvider` context with session state management
- [ ] 5.4 Create login/signup page with Supabase Auth UI components
- [ ] 5.5 Configure Google OAuth provider in Supabase dashboard and frontend
- [ ] 5.6 Configure GitHub OAuth provider in Supabase dashboard and frontend
- [ ] 5.7 Create user menu component (avatar, logout button)

## 6. Frontend Protected Routes
- [ ] 6.1 Create `useAuth` hook for accessing auth state
- [ ] 6.2 Create `ProtectedRoute` wrapper component
- [ ] 6.3 Update page layouts to include auth state
- [ ] 6.4 Add login redirect for unauthenticated access to protected routes
- [ ] 6.5 Update Dashboard to show only user's projects

## 7. Frontend API Integration
- [ ] 7.1 Update API client to include Authorization header with JWT
- [ ] 7.2 Add token refresh handling on 401 responses
- [ ] 7.3 Handle logout by clearing session and redirecting

## 8. Anonymous Trial Support
- [ ] 8.1 Generate temporary anonymous session ID for unauthenticated users
- [ ] 8.2 Allow project creation with anonymous user context
- [ ] 8.3 Implement anonymous project limit enforcement (max 3 projects)
- [ ] 8.4 Implement anonymous file upload limit enforcement (max 2 files)
- [ ] 8.5 Add "Sign in to save your work" and limit-reached prompts
- [ ] 8.6 Implement anonymous-to-authenticated data migration on login

## 9. Configuration & Documentation
- [ ] 9.1 Update `env.example` with new Supabase Auth variables
- [ ] 9.2 Update README with authentication setup instructions
- [ ] 9.3 Add AUTH_BYPASS_ENABLED flag for local development
- [ ] 9.4 Document breaking changes in CHANGELOG

## 10. Testing & Verification
- [ ] 10.1 Manual test: Login flow with email/password
- [ ] 10.2 Manual test: Protected routes redirect to login
- [ ] 10.3 Manual test: Project isolation between users
- [ ] 10.4 Manual test: Anonymous trial and conversion
- [ ] 10.5 Run existing test suite to verify no regressions
