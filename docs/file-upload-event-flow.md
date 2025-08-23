# File Upload Event Handling Flow

## Overview

This document describes the complete file upload event handling flow in the RAG knowledge management system, from upload confirmation to RAG processing completion.

## Architecture Components

### Key Files and Methods

| Component | File Path | Key Methods | Purpose |
|-----------|-----------|-------------|---------|
| **API Endpoint** | `modules/api/file_api.py` | `confirm_upload()` | Receives upload confirmation requests |
| **File Service** | `modules/file_upload/service.py` | `confirm_upload()` | Validates and confirms file uploads |
| **Task Service** | `modules/services/task_service.py` | `submit_task()` | Manages Celery task submission |
| **File Handler** | `modules/tasks/handlers/file_handlers.py` | `FileUploadCompleteHandler.handle()` | Processes upload confirmation events |
| **RAG Handler** | `modules/tasks/handlers/rag_handlers.py` | `DocumentProcessingHandler.handle()` | Processes RAG pipeline |
| **Worker** | `worker.py` | `main()` | Celery worker process |

## Complete Flow Diagram

```mermaid
graph TB
    Client[客户端] --> API[POST /files/confirm/{file_id}]
    
    subgraph "API Layer"
        API --> FileAPI[modules/api/file_api.py::confirm_upload]
        FileAPI --> TaskSubmit[_submit_task_async]
    end
    
    subgraph "Service Layer"
        FileAPI --> FileService[modules/file_upload/service.py::confirm_upload]
        FileService --> Storage[Storage Validation]
        FileService --> Database[(Database Update)]
    end
    
    subgraph "Task Queue (Redis)"
        TaskSubmit --> RedisQueue[Redis Task Queue]
        RedisQueue --> FileQueue[file_queue]
    end
    
    subgraph "Worker Process (worker.py)"
        FileQueue --> Worker[Celery Worker]
        Worker --> FileHandler[modules/tasks/handlers/file_handlers.py::FileUploadCompleteHandler]
    end
    
    subgraph "File Processing"
        FileHandler --> StorageCheck[Storage File Validation]
        StorageCheck --> Download[Download to Temp]
        Download --> LoadDoc[Factory Pattern Document Loading]
        LoadDoc --> CreateDoc[Create Document Record]
        CreateDoc --> TriggerRAG[Submit RAG Task]
    end
    
    subgraph "RAG Pipeline"
        TriggerRAG --> RAGQueue[rag_queue]
        RAGQueue --> RAGWorker[RAG Worker]
        RAGWorker --> RAGHandler[modules/tasks/handlers/rag_handlers.py::DocumentProcessingHandler]
        RAGHandler --> Chunking[Text Chunking]
        Chunking --> Embedding[Generate Embeddings]
        Embedding --> VectorStore[Store in Weaviate]
    end
    
    subgraph "Result Storage"
        FileHandler --> TaskResult[Task Result Serialization]
        TaskResult --> RedisResult[(Redis Result Backend)]
        RAGHandler --> RAGResult[RAG Task Result]
        RAGResult --> RedisResult
    end
```

## Detailed Process Steps

### 1. Upload Confirmation API (Entry Point)

**File:** `modules/api/file_api.py`  
**Method:** `confirm_upload()`  
**Line:** ~214-229

```python
async def confirm_upload(
    file_id: str,
    request: schemas.FileUploadConfirmRequest,
    file_service: FileService = Depends(get_file_service),
    task_service: CeleryTaskService = Depends(get_task_service),
):
    # Confirm upload via file service
    confirm_response = await file_service.confirm_upload(request)
    
    # Submit async task without blocking
    asyncio.create_task(
        _submit_task_async(
            task_service,
            schemas.TaskName.FILE_UPLOAD_CONFIRM.value,
            file_id=confirm_response.file_id,
            file_path=confirm_response.file_path,
        )
    )
```

### 2. File Service Validation

**File:** `modules/file_upload/service.py`  
**Method:** `confirm_upload()`  
**Purpose:** Validates file existence and updates database status

- Checks if file record exists in database
- Validates file exists in storage (MinIO/S3)
- Updates file status to `FileStatus.UPLOADED`
- Returns confirmation response with file details

### 3. Task Queue Submission

**File:** `modules/services/task_service.py`  
**Method:** `submit_task()`  
**Purpose:** Routes task to appropriate Celery queue

**Task Routing Configuration (Line ~488-508):**
```python
self.app.conf.task_routes = {
    # File processing tasks
    "file_upload_confirm": {"queue": "file_queue"},
    "TaskName.FILE_UPLOAD_CONFIRM": {"queue": "file_queue"},
    # RAG processing tasks  
    "rag.process_document_async": {"queue": "rag_queue"},
    # Other task routes...
}
```

### 4. File Upload Handler Execution

**File:** `modules/tasks/handlers/file_handlers.py`  
**Class:** `FileUploadCompleteHandler`  
**Method:** `handle()`  
**Lines:** ~155-273

**Key Processing Steps:**

#### 4.1 Storage Validation
```python
# Verify file exists in storage
file_exists = await storage.file_exists(file_path)
file_info = await storage.get_file_info(file_path)
```

#### 4.2 Document Processing with RAG
```python
document_processing_result = await self._process_document_with_rag(
    file_id=file_id,
    file_path=file_path, 
    file_size=file_size,
    storage=storage,
    **metadata,
)
```

#### 4.3 Document Loading (Lines ~275-304)
- Downloads file to temporary location
- Uses factory pattern to load document based on file type
- Supports PDF, TXT, DOC, DOCX, HTML, MD, JSON, CSV formats

#### 4.4 Database Operations (Lines ~401-504)
- Uses synchronous SQLAlchemy to avoid async context conflicts
- Creates document record with metadata
- Handles thread pool execution to isolate from Celery context

#### 4.5 RAG Pipeline Trigger (Lines ~459-489)
```python
# Submit RAG processing task
rag_task = current_app.send_task(
    "rag.process_document_async",
    kwargs={
        "file_id": file_id,
        "document_id": str(document_model.id),
        "file_path": file_path,
        "content_type": content_type,
        "topic_id": topic_id,
        "embedding_provider": "openai",
        "vector_store_provider": "weaviate",
    },
    queue="rag_queue",
    priority=1,
)
```

### 5. RAG Processing Pipeline

**File:** `modules/tasks/handlers/rag_handlers.py`  
**Class:** `DocumentProcessingHandler`  

**Processing Steps:**
1. **Text Processing:** Extract and clean text content
2. **Chunking:** Split text into semantic chunks
3. **Embedding Generation:** Create vector embeddings using OpenAI
4. **Vector Storage:** Store embeddings in Weaviate vector database
5. **Search Index:** Update search indices for retrieval

### 6. Result Serialization and Storage

**Critical Fix Applied:** HTTPHeaderDict Serialization  
**File:** `modules/tasks/handlers/file_handlers.py`  
**Function:** `sanitize_for_json_serialization()` (Lines ~29-69)

**Purpose:** Converts non-JSON-serializable objects (like HTTPHeaderDict from urllib3) to regular dictionaries before task result storage.

```python
def sanitize_for_json_serialization(obj: Any) -> Any:
    # Handle HTTPHeaderDict and other non-serializable objects
    if hasattr(obj, 'items') and callable(getattr(obj, 'items')):
        return {k: sanitize_for_json_serialization(v) for k, v in obj.items()}
    # Recursive sanitization...
```

## Worker Configuration

**File:** `worker.py`  
**Purpose:** Celery worker process with specialized queue handling

**Queue Specialization:**
- `file_queue`: Handles file processing tasks (concurrency=3)
- `rag_queue`: Handles RAG pipeline tasks (concurrency=2)  
- `document_queue`: Handles document operations (concurrency=4)
- `workflow_queue`: Handles workflow orchestration (concurrency=2)

**Worker Startup:**
```bash
./start_workers.sh --multi
```

## Error Handling and Monitoring

### Task Retry Configuration
- **Max Retries:** 3 attempts for file processing
- **Retry Delay:** Exponential backoff  
- **Timeout:** 300 seconds for file tasks, 180 seconds for content analysis

### Logging and Monitoring
- **Log Files:** `logs/worker_file_*.log`, `logs/worker_rag_*.log`
- **Task Status:** Tracked in Redis backend
- **Health Checks:** Built-in task monitoring and status endpoints

## Status Flow

```
File Upload → PENDING → UPLOADED → PROCESSING → COMPLETED
                 ↓         ↓           ↓           ↓
            Database   Task Queue   Worker    Result Storage
```

## Performance Considerations

1. **Async Processing:** Upload confirmation returns immediately, processing happens asynchronously
2. **Queue Isolation:** Different worker types handle different task categories
3. **Concurrency Control:** Worker concurrency tuned per task type
4. **Resource Management:** Temporary files cleaned up after processing
5. **Error Recovery:** Task retries with exponential backoff
6. **Memory Management:** Large files processed in streaming chunks

## Integration Points

- **Storage Backend:** MinIO S3-compatible storage
- **Message Queue:** Redis for Celery broker and result backend
- **Vector Database:** Weaviate for embedding storage  
- **Search Engine:** Elasticsearch for full-text search
- **Database:** PostgreSQL for metadata and relationships

This architecture provides a robust, scalable file processing pipeline with proper error handling, monitoring, and performance optimization.