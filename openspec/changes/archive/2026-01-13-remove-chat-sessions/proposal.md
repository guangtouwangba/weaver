# Change: Remove Chat Sessions - Simplify to Single Conversation History

## Why
Chat sessions feature was implemented but the frontend UI never exposed session switching functionality. Users cannot see or switch between sessions, making the feature dead code. Simplifying to a single conversation history per project reduces complexity and maintenance burden.

## What Changes
- **BREAKING**: Remove `chat_sessions` table and `session_id` from `chat_messages`
- Remove session management APIs (`/chat/sessions/*`)
- Remove session-related DTOs and entities
- Simplify frontend to use project-level chat history directly
- Remove session state management from StudioContext

## Impact
- Affected specs: chat (if exists)
- Affected code:
  - Backend: `api/v1/chat.py`, `dto/chat.py`, `entities/chat.py`, `use_cases/chat/*`
  - Frontend: `StudioContext.tsx`, `AssistantPanel.tsx`, `ChatOverlay.tsx`, `api.ts`
  - Database: Migration to drop `chat_sessions` table and `session_id` column
