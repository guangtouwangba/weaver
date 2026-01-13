# Tasks: Remove Chat Sessions

## 1. Database Migration
- [x] 1.1 Create migration to drop `session_id` foreign key from `chat_messages`
- [x] 1.2 Drop `session_id` column from `chat_messages`
- [x] 1.3 Drop `chat_sessions` table

## 2. Backend Changes
- [x] 2.1 Remove `ChatSession` entity from `domain/entities/chat.py`
- [x] 2.2 Remove `session_id` from `ChatMessage` entity
- [x] 2.3 Remove session DTOs from `dto/chat.py` (CreateSessionRequest, UpdateSessionRequest, SessionResponse, SessionListResponse)
- [x] 2.4 Remove `session_id` from SendMessageRequest and ChatResponse DTOs
- [x] 2.5 Remove session management use cases (`session_management.py`)
- [x] 2.6 Remove session API endpoints from `api/v1/chat.py`
- [x] 2.7 Update `send_message.py` to remove session_id handling
- [x] 2.8 Update `stream_message.py` to remove session_id handling
- [x] 2.9 Update chat history retrieval to work without sessions

## 3. Frontend Changes
- [x] 3.1 Remove session types from `api.ts` (ChatSession, ChatSessionListResponse)
- [x] 3.2 Remove session API calls from `api.ts` (createSession, listSessions, etc.)
- [x] 3.3 Remove session state from `StudioContext.tsx` (chatSessions, activeSessionId, etc.)
- [x] 3.4 Remove session management functions from `StudioContext.tsx`
- [x] 3.5 Update `AssistantPanel.tsx` to remove session references
- [x] 3.6 Update `ChatOverlay.tsx` to remove session references
- [x] 3.7 Update chat message sending to not include session_id

## 4. Cleanup
- [x] 4.1 Remove unused imports
- [ ] 4.2 Test chat functionality works without sessions
