# auth Specification

## Purpose
TBD - created by archiving change add-supabase-auth. Update Purpose after archive.
## Requirements
### Requirement: User Authentication
The system SHALL authenticate users via Supabase Auth before granting access to protected resources, supporting email/password and OAuth providers.

#### Scenario: Successful login with email/password
- **WHEN** a user submits valid email and password credentials
- **THEN** Supabase Auth validates the credentials
- **AND** a JWT access token is returned
- **AND** the user is redirected to the Dashboard

#### Scenario: Successful login with Google OAuth
- **WHEN** a user clicks "Sign in with Google"
- **THEN** the user is redirected to Google OAuth consent screen
- **WHEN** the user grants permission
- **THEN** a JWT access token is returned
- **AND** the user is redirected to the Dashboard

#### Scenario: Successful login with GitHub OAuth
- **WHEN** a user clicks "Sign in with GitHub"
- **THEN** the user is redirected to GitHub OAuth authorization page
- **WHEN** the user grants permission
- **THEN** a JWT access token is returned
- **AND** the user is redirected to the Dashboard

#### Scenario: Failed login with invalid credentials
- **WHEN** a user submits invalid email or password
- **THEN** an error message is displayed
- **AND** the user remains on the login page

#### Scenario: User logout
- **WHEN** a user clicks the logout button
- **THEN** the session is terminated
- **AND** the JWT token is cleared
- **AND** the user is redirected to the login page

### Requirement: JWT Token Verification

The backend API SHALL verify Supabase JWT tokens on protected endpoints, **including WebSocket connections**.

#### Scenario: Valid JWT token on WebSocket connection

- **WHEN** a WebSocket connection request includes a valid `token` query parameter
- **THEN** the backend extracts the user_id from the JWT payload
- **AND** the WebSocket connection is accepted with authenticated user context

#### Scenario: Missing JWT token on WebSocket connection

- **WHEN** a WebSocket connection request lacks a `token` query parameter
- **AND** `AUTH_BYPASS_ENABLED` is false
- **THEN** the WebSocket connection is accepted with anonymous user context
- **AND** access is limited to anonymous-created resources

#### Scenario: Invalid JWT token on WebSocket connection

- **WHEN** a WebSocket connection request includes an invalid or expired `token` query parameter
- **THEN** the WebSocket connection is closed with code 1008 (Policy Violation)
- **AND** the error reason is included in the close message

---

### Requirement: User-Scoped Project Access

The system SHALL verify project ownership on every project-scoped endpoint before granting access to resources.

#### Scenario: Access denied for chat on non-owned project
- **WHEN** a user sends a chat message to a project they do not own
- **THEN** the system returns HTTP 403 Forbidden
- **AND** no chat message is processed

#### Scenario: Access denied for output generation on non-owned project
- **WHEN** a user requests output generation on a project they do not own
- **THEN** the system returns HTTP 403 Forbidden
- **AND** no generation task is started

#### Scenario: Access denied for canvas data on non-owned project
- **WHEN** a user requests canvas data from a project they do not own
- **THEN** the system returns HTTP 403 Forbidden
- **AND** no canvas data is returned

#### Scenario: Access denied for URL extraction on non-owned project
- **WHEN** a user submits a URL for extraction to a project they do not own
- **THEN** the system returns HTTP 403 Forbidden
- **AND** no extraction task is created

#### Scenario: Access denied for document confirmation on non-owned project
- **WHEN** a user confirms a document upload to a project they do not own
- **THEN** the system returns HTTP 403 Forbidden
- **AND** no document record is created

### Requirement: User-Scoped File Storage
The system SHALL store user files in isolated storage paths.

#### Scenario: Upload file to user-scoped path
- **WHEN** an authenticated user uploads a file
- **THEN** the file is stored at path `{user_id}/{project_id}/{filename}`
- **AND** the file is not accessible to other users

#### Scenario: Download file with ownership verification
- **WHEN** a user requests to download a file
- **THEN** the system verifies the user owns the parent project
- **AND** only allows download if ownership is confirmed

### Requirement: Anonymous Trial Mode
The system SHALL allow unauthenticated users to trial the application with limited resources and persistence.

#### Scenario: Anonymous user creates project
- **WHEN** an unauthenticated user creates a project
- **THEN** the project is created with an anonymous session identifier
- **AND** the project is accessible for the current browser session
- **AND** a prompt suggests signing in to save work permanently

#### Scenario: Anonymous project limit
- **WHEN** an anonymous user has already created 3 projects
- **AND** attempts to create a new project
- **THEN** the system displays a message requiring sign-in to create more projects
- **AND** the project creation is blocked

#### Scenario: Anonymous file upload limit
- **WHEN** an anonymous user has already uploaded 2 files across all projects
- **AND** attempts to upload another file
- **THEN** the system displays a message requiring sign-in to upload more files
- **AND** the file upload is blocked

#### Scenario: Anonymous data conversion on login
- **WHEN** an anonymous user signs in or creates an account
- **THEN** the system offers to migrate anonymous session data to the authenticated account
- **AND** the user can choose to migrate or discard anonymous data
- **AND** the resource limits are removed after successful authentication

#### Scenario: Anonymous data cleanup
- **WHEN** anonymous session data has not been accessed for 7 days
- **THEN** the system automatically deletes the anonymous data
- **AND** associated files are removed from storage

### Requirement: Protected Routes
The frontend SHALL protect routes that require authentication.

#### Scenario: Unauthenticated access to protected route
- **WHEN** an unauthenticated user navigates to a protected route (e.g., /studio)
- **THEN** the user is redirected to the login page
- **AND** the original destination is preserved for post-login redirect

#### Scenario: Authenticated access to protected route
- **WHEN** an authenticated user navigates to a protected route
- **THEN** the page loads normally with user context available

### Requirement: Development Mode Auth Bypass
The system SHALL support bypassing authentication in local development environments.

#### Scenario: Auth bypass enabled
- **WHEN** the `AUTH_BYPASS_ENABLED` environment variable is set to `true`
- **THEN** all API requests are treated as authenticated with a default development user
- **AND** the frontend skips login redirect for protected routes

#### Scenario: Auth bypass disabled in production
- **WHEN** the `ENVIRONMENT` is set to `production`
- **THEN** the `AUTH_BYPASS_ENABLED` variable is ignored
- **AND** authentication is always enforced

### Requirement: Frontend WebSocket Authentication

The frontend SHALL include authentication tokens in all WebSocket connection URLs.

#### Scenario: Authenticated user connects to Canvas WebSocket

- **WHEN** an authenticated user opens the Studio page
- **THEN** the frontend retrieves the current access token
- **AND** appends `?token={access_token}` to the WebSocket URL
- **AND** connects to the Canvas WebSocket with authentication

#### Scenario: Authenticated user connects to Output WebSocket

- **WHEN** an authenticated user triggers content generation (mindmap, summary)
- **THEN** the frontend retrieves the current access token
- **AND** appends `token={access_token}` to the WebSocket URL (preserving existing query params)
- **AND** connects to the Output WebSocket with authentication

#### Scenario: Authenticated user connects to Document WebSocket

- **WHEN** an authenticated user uploads a document
- **THEN** the frontend retrieves the current access token
- **AND** appends `?token={access_token}` to the WebSocket URL
- **AND** connects to the Document WebSocket with authentication

#### Scenario: Anonymous user connects to WebSocket

- **WHEN** an unauthenticated user opens the Studio page
- **THEN** the frontend connects to WebSocket without a token parameter
- **AND** the connection is accepted with anonymous user context

