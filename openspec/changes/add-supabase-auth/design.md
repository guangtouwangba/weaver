# Design: Supabase Authentication Integration

## Context
The Visual Thinking Assistant needs multi-user support for open-source and commercial deployment. Supabase provides a complete auth solution with JWT-based authentication, which integrates well with the existing Supabase Storage infrastructure.

### Stakeholders
- End users: Need secure, private workspaces
- Solo developer: Needs low-maintenance auth solution
- Open-source contributors: Need easy local development setup

## Goals / Non-Goals

### Goals
- User authentication via Supabase Auth (email/password, OAuth providers)
- User-scoped project and resource isolation
- Anonymous trial experience with conversion to authenticated user
- Compatible with local development (optional auth bypass)

### Non-Goals
- RBAC/team collaboration (future enhancement)
- Custom auth provider integration
- User profile management beyond basic auth

## Decisions

### D1: Full-Stack Supabase Auth
- **Decision**: Use Supabase Auth on both frontend (Auth UI) and backend (JWT verification)
- **Why**: Consistent auth flow, official SDK support, reduces custom code
- **Alternative**: Backend-only auth with custom frontend forms - rejected for increased complexity

### D2: User-Owns-Projects Model
- **Decision**: Add `user_id` to `projects` table, filter all project queries by user
- **Why**: Simple ownership model, minimal schema changes, clear isolation
- **Alternative**: RBAC with permissions table - rejected as over-engineering for solo developer

### D3: Path Prefix File Isolation
- **Decision**: Storage paths become `{user_id}/{project_id}/{filename}`
- **Why**: Works with existing Supabase Storage bucket, RLS policies possible
- **Alternative**: Separate buckets per user - rejected for operational complexity

### D4: Soft Login with Anonymous Trial (Limited)
- **Decision**: Allow unauthenticated users to create/use projects with resource limits
- **Why**: Lower friction for first-time users, converts to authenticated on value demonstration
- **Limits**: Max 3 projects, max 2 file uploads total
- **Implementation**:
  - Anonymous sessions use temporary `anon-{session_id}` user ID
  - Track project/file counts per anonymous session
  - Data stored normally but marked as anonymous
  - On login, optionally migrate anonymous data to authenticated user
  - Anonymous data cleaned up after 7 days

### D5: JWT Verification Approach
- **Decision**: Verify Supabase JWT using `supabase-py` library or manual JWKS verification
- **Implementation**:
  ```python
  # FastAPI dependency
  async def get_current_user(
      authorization: str = Header(None)
  ) -> Optional[str]:
      if not authorization or not authorization.startswith("Bearer "):
          return None  # Anonymous user
      token = authorization.split(" ")[1]
      # Verify JWT and extract user_id
      payload = verify_supabase_jwt(token)
      return payload["sub"]  # Supabase user UUID
  ```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Auth UI     │    │  Auth Store  │    │  API Client  │  │
│  │  (Supabase)  │───▶│  (Context)   │───▶│  (+JWT)      │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ Authorization: Bearer <JWT>
┌─────────────────────────────────────────────────────────────┐
│                        Backend                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Auth        │    │  User        │    │  Project     │  │
│  │  Middleware  │───▶│  Context     │───▶│  Repository  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                                        │          │
│         ▼                                        ▼          │
│  ┌──────────────┐                       ┌──────────────┐   │
│  │  JWT Verify  │                       │  user_id     │   │
│  │  (Supabase)  │                       │  Filter      │   │
│  └──────────────┘                       └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema Changes

```sql
-- Add user_id to projects table
ALTER TABLE projects ADD COLUMN user_id VARCHAR(255);
CREATE INDEX idx_projects_user_id ON projects(user_id);

-- Existing data migration: not needed (clean slate)
```

## Storage Path Convention

```
Before: data/uploads/{project_id}/{filename}
After:  data/uploads/{user_id}/{project_id}/{filename}

Supabase Storage:
Before: {bucket}/{project_id}/{filename}
After:  {bucket}/{user_id}/{project_id}/{filename}
```

## Environment Variables

```bash
# New variables for auth
SUPABASE_URL=https://your-project.supabase.co  # Already exists
SUPABASE_ANON_KEY=eyJ...                        # Public anon key for frontend
SUPABASE_JWT_SECRET=your-jwt-secret             # For backend JWT verification

# Optional: local development bypass
AUTH_BYPASS_ENABLED=false  # Set true for local dev without auth
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Auth adds latency to every request | JWT verification is fast (~1ms), cache decoded tokens |
| Anonymous data accumulation | Cron job to clean up after 7 days |
| Breaking change for existing users | Clean slate migration, document in changelog |
| Complexity for local development | AUTH_BYPASS_ENABLED flag for dev mode |

## Migration Plan

1. **Pre-migration**: Document breaking change in CHANGELOG
2. **Database**: Drop and recreate with new schema (clean slate)
3. **Backend**: Deploy with auth middleware (graceful degradation if no token)
4. **Frontend**: Deploy with auth UI and protected routes
5. **Rollback**: Remove auth middleware, restore old schema

## Resolved Decisions

- **OAuth Providers**: Initial release supports Google and GitHub OAuth
- **Anonymous Limits**: Anonymous trial limited to 3 projects and 2 file uploads

