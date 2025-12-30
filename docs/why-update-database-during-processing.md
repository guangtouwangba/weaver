# Why Update Database During Document Processing?

## Overview

During document processing, the system updates the database at multiple stages. This document explains **why** these updates are necessary and what problems they solve.

## Database Updates During Processing

### 1. Status Updates

```python
# Step 1: Update to PROCESSING
await self._update_document_status(session, document_id, DocumentStatus.PROCESSING)

# Step 5: Update to READY
await self._update_document_status(fresh_session, document_id, DocumentStatus.READY, page_count=page_count)

# On Error: Update to ERROR
await self._update_document_status(fresh_session, document_id, DocumentStatus.ERROR)
```

**Status Flow**: `pending → processing → ready` (or `error`)

### 2. Content Updates

```python
# Save summary (if generated)
update(DocumentModel).values(summary=summary)

# Save full content and metadata
update(DocumentModel).values(
    full_content=full_content,
    content_token_count=token_count,
    parsing_metadata=parsing_metadata,
)
```

### 3. Metadata Updates

```python
# Update page count
update(DocumentModel).values(page_count=page_count)
```

## Why These Updates Are Necessary

### 1. **Frontend State Management**

The frontend needs to display document status and information to users:

```typescript
// Frontend queries document list
const { items } = await documentsApi.list(projectId);

// Each document has:
interface ProjectDocument {
  id: string;
  status: 'pending' | 'processing' | 'ready' | 'error';
  page_count: number;
  summary?: string;
  // ...
}
```

**Without database updates**:
- Frontend would show stale status (always "pending")
- Users can't see processing progress
- No way to know when document is ready

**With database updates**:
- Frontend can query current status
- Users see real-time progress
- UI can show "Processing..." or "Ready" states

### 2. **Data Persistence & Recovery**

Processing can take **minutes** (OCR, embedding generation). If the worker crashes:

**Without database updates**:
- All processing progress is lost
- Must restart from beginning
- No way to know what was completed

**With database updates**:
- Status persists across restarts
- Can resume from last checkpoint
- Error messages saved for debugging

**Example**: If embedding generation fails at chunk 500/1000:
- Database shows `status="error"` with error message
- Can retry or investigate the issue
- User sees error instead of infinite "processing"

### 3. **WebSocket Notifications Are Not Persistent**

WebSocket provides real-time updates, but:

```python
# WebSocket notification
await document_notification_service.notify_document_status(
    project_id=str(project_id),
    document_id=str(document_id),
    status="ready",
    summary=summary,
    page_count=page_count,
)
```

**Problems with WebSocket-only approach**:
- ❌ If client disconnects, misses the update
- ❌ New clients connecting later don't get status
- ❌ No historical record of status changes
- ❌ Can't query status via REST API

**Database as source of truth**:
- ✅ Persistent across disconnections
- ✅ New clients can query current status
- ✅ Historical record in database
- ✅ REST API always returns current state

### 4. **Frontend Query Patterns**

The frontend uses multiple patterns to get document information:

#### Pattern 1: Initial Load (REST API)
```typescript
// Page load: Get all documents
const documents = await documentsApi.list(projectId);
// Returns documents with current status from database
```

#### Pattern 2: Real-time Updates (WebSocket)
```typescript
// Subscribe to updates
useDocumentWebSocket({
  projectId,
  onDocumentStatusChange: (event) => {
    // Update local state
    setDocuments(prev => prev.map(doc => 
      doc.id === event.document_id 
        ? { ...doc, status: event.status, ... }
        : doc
    ));
  },
});
```

#### Pattern 3: Refresh/Reconnect (REST API)
```typescript
// User refreshes page or reconnects
// WebSocket connection lost, need to query database
const documents = await documentsApi.list(projectId);
```

**Without database updates**: Pattern 1 and 3 would return stale data.

### 5. **Error Handling & Debugging**

When processing fails:

```python
except Exception as e:
    # Update status to ERROR
    await self._update_document_status(
        fresh_session,
        document_id,
        status=DocumentStatus.ERROR,
    )
    # Error message saved in database
```

**Benefits**:
- User sees error message in UI
- Support team can query error details
- Can retry failed documents
- Debugging: know exactly where processing failed

### 6. **Incremental Data Availability**

Processing generates data at different stages:

1. **After parsing**: `page_count` available
2. **After summary generation**: `summary` available
3. **After chunking**: `parsing_metadata` available
4. **After full content save**: `full_content`, `content_token_count` available

**Why save incrementally**:
- Frontend can show partial information (e.g., "10 pages extracted")
- If processing fails later, at least have page count
- Better UX: show progress as data becomes available

**Example**:
```typescript
// User sees in UI:
// "Processing... 10 pages extracted"
// Even if embedding generation fails later
```

### 7. **Multi-Worker Coordination**

Multiple workers can process different documents:

**Without database updates**:
- Workers can't coordinate
- No way to know if another worker is processing
- Risk of duplicate processing

**With database updates**:
- Status acts as lock (`processing` = being processed)
- Other workers skip documents in `processing` state
- Can implement retry logic for stuck tasks

### 8. **API Response Consistency**

REST API endpoints return database state:

```python
@router.get("/projects/{project_id}/documents")
async def list_documents(...):
    # Query database
    documents = await document_repo.find_by_project(project_id)
    # Returns current status from database
    return DocumentListResponse(items=documents)
```

**Without database updates**: API would return incorrect status.

## What Gets Updated and When

| Stage | Database Update | Why |
|-------|----------------|-----|
| **Start Processing** | `status = "processing"` | Signal that processing started |
| **After Summary** | `summary = "..."` | Save summary for UI display |
| **After Full Content** | `full_content`, `content_token_count`, `parsing_metadata` | Save for long_context RAG mode |
| **After Chunks** | `DocumentChunkModel` records | Save chunks for retrieval |
| **Complete** | `status = "ready"`, `page_count = N` | Signal completion, save metadata |
| **On Error** | `status = "error"`, `error_message = "..."` | Signal failure, save error info |

## Alternative Approaches (and why they don't work)

### ❌ Option 1: Only Update at End

**Problem**: 
- No progress visibility
- If crash, lose all progress
- Frontend shows stale status

### ❌ Option 2: Only Use WebSocket

**Problem**:
- Not persistent
- Lost on disconnect
- Can't query via REST API

### ❌ Option 3: In-Memory State Only

**Problem**:
- Lost on restart
- Not accessible from other workers
- No historical record

## Best Practice: Database as Source of Truth

The current design follows the **Database as Source of Truth** pattern:

1. **Database** = Persistent, queryable state
2. **WebSocket** = Real-time notifications (optimistic updates)
3. **REST API** = Query current state from database

This provides:
- ✅ **Persistence**: Survives restarts
- ✅ **Queryability**: Can query current state
- ✅ **Real-time**: WebSocket for instant updates
- ✅ **Reliability**: Database is authoritative source

## Summary

Database updates during processing are necessary because:

1. **Frontend needs current status** - Users see processing progress
2. **Data persistence** - Survive crashes and restarts
3. **WebSocket is not persistent** - Need database as source of truth
4. **Error handling** - Save error messages for debugging
5. **Incremental availability** - Show partial progress
6. **Multi-worker coordination** - Status acts as coordination mechanism
7. **API consistency** - REST API returns database state

Without these updates, the system would have:
- No way to show processing status
- Lost progress on crashes
- No error information
- Inconsistent API responses
- Poor user experience











