# File Upload Event Handling - Key Components Reference

## Core Files and Methods

### 1. API Entry Point
**File:** `modules/api/file_api.py`
- **Method:** `confirm_upload(file_id, request, file_service, task_service)`
  - **Lines:** 214-229
  - **Purpose:** HTTP endpoint for upload confirmation
  - **Key Action:** Submits `file_upload_confirm` task asynchronously

- **Method:** `_submit_task_async(task_service, task_name, **kwargs)`
  - **Lines:** 283-295
  - **Purpose:** Async task submission without blocking main flow

### 2. File Service Layer
**File:** `modules/file_upload/service.py`
- **Method:** `confirm_upload(file_id, actual_size, file_hash)`
  - **Lines:** ~200-250
  - **Purpose:** Validates file existence and updates database status
  - **Key Actions:**
    - Validates file exists in storage
    - Updates file status to `UPLOADED`
    - Returns file metadata

### 3. Task Service
**File:** `modules/services/task_service.py`
- **Method:** `submit_task(task_name, **kwargs)`
  - **Lines:** ~350-370
  - **Purpose:** Routes tasks to appropriate Celery queues

- **Method:** `_setup_task_routing()`
  - **Lines:** 485-520
  - **Purpose:** Configures task-to-queue routing
  - **Key Configuration:**
    ```python
    "file_upload_confirm": {"queue": "file_queue"}
    "rag.process_document_async": {"queue": "rag_queue"}
    ```

### 4. Main Task Handler
**File:** `modules/tasks/handlers/file_handlers.py`
- **Class:** `FileUploadCompleteHandler`
- **Method:** `handle(file_id, file_path, **metadata)`
  - **Lines:** 155-273
  - **Purpose:** Main file processing logic
  - **Key Actions:**
    1. Validate file in storage
    2. Process document with RAG pipeline
    3. Return sanitized result

- **Method:** `_process_document_with_rag(file_id, file_path, file_size, storage, **metadata)`
  - **Lines:** 275-304
  - **Purpose:** Document processing orchestration
  - **Key Actions:**
    1. Download file to temp location
    2. Load document using factory pattern
    3. Create document record and trigger RAG

- **Method:** `_download_file_to_temp(storage, file_path, file_id)`
  - **Lines:** 306-336
  - **Purpose:** Download file from storage to temporary local file

- **Method:** `_load_document(file_path, file_id, metadata)`
  - **Lines:** 338-361
  - **Purpose:** Load document using factory pattern based on file type

- **Method:** `_create_document_and_process_rag(document, file_id, file_path, file_size, metadata)`
  - **Lines:** 363-399
  - **Purpose:** Thread pool execution for database operations

- **Method:** `_create_document_with_new_loop(document, file_id, file_path, file_size, metadata)`
  - **Lines:** 401-504
  - **Purpose:** Synchronous database operations to avoid async context conflicts
  - **Key Actions:**
    1. Create document record in PostgreSQL
    2. Submit RAG processing task
    3. Return processing metadata

- **Function:** `sanitize_for_json_serialization(obj)`
  - **Lines:** 29-69
  - **Purpose:** Convert non-JSON-serializable objects (HTTPHeaderDict) to regular dicts
  - **Critical Fix:** Prevents Celery result serialization errors

### 5. Document Loading Factory
**File:** `modules/file_loader/factory.py`
- **Method:** `get_loader(content_type)`
  - **Purpose:** Returns appropriate loader based on file type
  - **Supported Types:** PDF, TXT, DOC, DOCX, HTML, MD, JSON, CSV

**File:** `modules/tasks/handlers/file_handlers.py`
- **Function:** `load_document_from_path_with_factory(file_path, **kwargs)`
  - **Lines:** 72-138
  - **Purpose:** Factory pattern implementation for document loading
  - **Key Features:**
    - Content type detection from file extension
    - Fallback to text loader if specific loader fails
    - Metadata enrichment

### 6. RAG Processing Handler
**File:** `modules/tasks/handlers/rag_handlers.py`
- **Class:** `DocumentProcessingHandler`
- **Method:** `handle(file_id, document_id, file_path, content_type, topic_id, embedding_provider, vector_store_provider)`
  - **Purpose:** RAG pipeline execution
  - **Key Actions:**
    1. Text processing and chunking
    2. Generate embeddings using OpenAI
    3. Store vectors in Weaviate
    4. Update search indices

### 7. Worker Process
**File:** `worker.py`
- **Function:** `main()`
  - **Lines:** 100-200
  - **Purpose:** Celery worker initialization and startup
  - **Key Features:**
    - Enhanced logging setup
    - Queue specialization configuration
    - Task routing setup

- **Function:** `setup_enhanced_logging(loglevel)`
  - **Lines:** 30-80
  - **Purpose:** Configure detailed worker logging

**File:** `start_workers.sh`
- **Function:** Multi-worker startup script
- **Purpose:** Start specialized workers for different task types
- **Worker Types:**
  - File Worker: `file_queue` (concurrency: 3)
  - RAG Worker: `rag_queue` (concurrency: 2)
  - Document Worker: `document_queue` (concurrency: 4)
  - Workflow Worker: `workflow_queue` (concurrency: 2)

### 8. Storage Integration
**File:** `modules/storage/minio_storage.py`
- **Method:** `file_exists(file_key)`
  - **Lines:** 198-209
  - **Purpose:** Check if file exists in MinIO storage

- **Method:** `get_file_info(file_key)`
  - **Lines:** 211-253
  - **Purpose:** Get file metadata from storage
  - **Returns:** File size, content type, last modified, etc.

- **Method:** `read_file(file_key)`
  - **Lines:** 255-281
  - **Purpose:** Read file content as bytes

### 9. Database Models
**File:** `modules/database/models.py`
- **Class:** `Document`
  - **Purpose:** Document record in PostgreSQL
  - **Key Fields:** id, title, content, content_type, file_id, file_path, metadata

**File:** `modules/repository/file_repository.py`
- **Method:** `get_file_by_id(file_id)`
  - **Purpose:** Retrieve file record from database

### 10. Configuration
**File:** `config/settings.py`
- **Class:** `CeleryConfig`
  - **Purpose:** Celery broker and result backend configuration
  - **Key Settings:**
    - Broker URL: Redis connection
    - Result backend: Redis connection
    - Serialization: JSON (prevents HTTPHeaderDict issues)

## Processing Flow Summary

1. **API Request** → `modules/api/file_api.py::confirm_upload()`
2. **File Validation** → `modules/file_upload/service.py::confirm_upload()`
3. **Task Submission** → `modules/services/task_service.py::submit_task()`
4. **Queue Routing** → Redis `file_queue`
5. **Worker Processing** → `worker.py` File Worker
6. **Handler Execution** → `modules/tasks/handlers/file_handlers.py::FileUploadCompleteHandler.handle()`
7. **Document Processing** → Factory pattern document loading
8. **Database Creation** → Sync SQLAlchemy document record creation
9. **RAG Trigger** → Submit `rag.process_document_async` to `rag_queue`
10. **RAG Processing** → `modules/tasks/handlers/rag_handlers.py::DocumentProcessingHandler.handle()`
11. **Result Storage** → Sanitized JSON results stored in Redis backend

## Critical Components for Troubleshooting

- **Task Registration:** `modules/services/task_service.py::_import_task_handlers()`
- **Queue Routing:** `modules/services/task_service.py::_setup_task_routing()`
- **Serialization Fix:** `modules/tasks/handlers/file_handlers.py::sanitize_for_json_serialization()`
- **Worker Status:** Log files in `logs/worker_*_*.log`
- **Task Results:** Redis backend with JSON serialization

## Monitoring and Debugging

- **Worker Logs:** `logs/worker_file_*.log`, `logs/worker_rag_*.log`
- **Task Status:** Redis keys for task states and results
- **Health Checks:** Built-in task monitoring endpoints
- **Error Tracking:** Comprehensive exception handling and logging throughout pipeline