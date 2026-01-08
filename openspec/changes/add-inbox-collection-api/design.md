# Design: Universal Inbox Collection API

## Context
The Visual Thinking Assistant needs a universal collection interface that allows users to capture content from anywhere - web browsers, mobile devices, automation tools (Apple Shortcuts), and third-party services. The existing inbox implementation provides basic CRUD operations but lacks the robustness needed for external integrations.

## Goals
- Provide a secure, well-documented API for external content collection
- Support multiple content types with platform-specific metadata
- Enable real-time preview of collected items in the Inbox UI
- Allow easy project assignment workflow
- Extensible design for future integrations (Zapier, IFTTT, etc.)

## Non-Goals
- Full OAuth2 implementation (API keys are sufficient for v1)
- Content processing/transformation in the collection endpoint
- Real-time sync between devices

## Decisions

### 1. API Authentication: API Keys
**Decision**: Use simple API keys stored per-user, manageable via settings UI.
**Rationale**: Simpler than OAuth, sufficient for personal integrations like browser extensions and shortcuts.
**Alternatives considered**:
- OAuth2: Too complex for v1, overkill for single-user integrations
- JWT tokens: Requires refresh logic, complicates extension development

### 2. Collection Endpoint Schema
**Decision**: Use a unified schema with platform-specific metadata in a `metadata` field.
```json
{
  "type": "article" | "video" | "link" | "note" | "pdf",
  "title": "string",
  "source_url": "string?",
  "content": "string?",
  "thumbnail_url": "string?",
  "source_type": "chrome_extension" | "ios_shortcut" | "api" | "manual",
  "tags": ["string"],
  "metadata": {
    "platform": "youtube" | "douyin" | "twitter" | null,
    "video_id": "string?",
    "duration": "number?",
    "channel_name": "string?",
    ...
  }
}
```
**Rationale**: Allows extending metadata without schema changes.

### 3. Preview Generation
**Decision**: Preview content is fetched on-demand in the frontend using the existing URL extractor.
**Rationale**: Keeps collection endpoint fast, leverages existing infrastructure.

### 4. Project Assignment Flow
**Decision**: Two-step process:
1. Collect to Inbox (fast, async)
2. Triage: Preview → Select Project → Add (or Create New Project → Add)

**Rationale**: Separates capture from organization, matches "Inbox Zero" methodology.

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/inbox/collect` | POST | Collect single item (requires API key) |
| `/api/v1/inbox/collect/batch` | POST | Collect multiple items (requires API key) |
| `/api/v1/inbox/items` | GET | List inbox items with filters |
| `/api/v1/inbox/items/{id}` | GET | Get single item detail |
| `/api/v1/inbox/items/{id}` | PATCH | Update item (mark read, add tags) |
| `/api/v1/inbox/items/{id}` | DELETE | Delete item |
| `/api/v1/inbox/items/{id}/assign/{project_id}` | POST | Assign to project |
| `/api/v1/settings/api-keys` | GET/POST/DELETE | Manage API keys |

## Risks / Trade-offs

- **API Key Security**: Keys can be leaked from browser extensions. Mitigation: Allow key revocation, show last-used timestamp.
- **Rate Limiting**: Not implemented in v1. Consider adding if abuse occurs.
- **Large Content**: `content` field could be very large for PDFs. Mitigation: Limit to first 10KB, store full content separately if needed.

## Open Questions

- Should we support file uploads via the collection API or only URLs?
- Should tags be auto-created if they don't exist, or require pre-creation?

