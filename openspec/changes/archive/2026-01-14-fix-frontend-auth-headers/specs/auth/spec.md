# Auth Specification Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
