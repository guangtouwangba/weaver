"""
Enhanced Swagger documentation for the RAG API.

Provides detailed documentation, examples, and schemas
for all API endpoints including the new task processing system.
"""

from typing import Dict, Any

# Task Processing API Examples
TASK_EXAMPLES = {
    "submit_task_request": {
        "summary": "Submit file for embedding processing",
        "description": "Submit a file for automatic embedding and processing",
        "value": {
            "file_id": "file_abc123",
            "file_path": "/uploads/documents/research_paper.pdf",
            "file_name": "AI Research Paper.pdf",
            "file_size": 2048000,
            "mime_type": "application/pdf",
            "topic_id": 42,
            "user_id": "user_456",
            "task_types": ["file_embedding", "document_parsing"],
            "priority": "normal",
            "custom_config": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "embedding_model": "text-embedding-ada-002"
            }
        }
    },
    "submit_task_response": {
        "summary": "Successful task submission",
        "description": "Response when tasks are successfully submitted",
        "value": {
            "success": True,
            "task_ids": ["task_uuid_1", "task_uuid_2"],
            "message": "Successfully submitted 2 tasks for processing"
        }
    },
    "task_status_response": {
        "summary": "Task status with progress",
        "description": "Detailed task status including progress information",
        "value": {
            "task_id": "task_uuid_1",
            "task_type": "file_embedding",
            "status": "processing",
            "file_name": "AI Research Paper.pdf",
            "progress": {
                "current_step": 3,
                "total_steps": 6,
                "percentage": 50.0,
                "current_operation": "生成向量嵌入",
                "estimated_remaining_seconds": 120
            },
            "created_at": "2024-01-15T10:30:00Z",
            "started_at": "2024-01-15T10:30:05Z",
            "completed_at": None,
            "error": None
        }
    },
    "topic_tasks_response": {
        "summary": "Tasks for a topic",
        "description": "List of tasks associated with a topic",
        "value": [
            {
                "task_id": "task_uuid_1",
                "task_type": "file_embedding",
                "status": "completed",
                "file_name": "document1.pdf",
                "progress": {
                    "current_step": 6,
                    "total_steps": 6,
                    "percentage": 100.0,
                    "current_operation": "完成",
                    "estimated_remaining_seconds": None
                },
                "created_at": "2024-01-15T10:30:00Z",
                "started_at": "2024-01-15T10:30:05Z",
                "completed_at": "2024-01-15T10:32:15Z",
                "error": None
            },
            {
                "task_id": "task_uuid_2",
                "task_type": "document_parsing",
                "status": "processing",
                "file_name": "document2.docx",
                "progress": {
                    "current_step": 2,
                    "total_steps": 4,
                    "percentage": 50.0,
                    "current_operation": "提取文本和元数据",
                    "estimated_remaining_seconds": 60
                },
                "created_at": "2024-01-15T10:35:00Z",
                "started_at": "2024-01-15T10:35:02Z",
                "completed_at": None,
                "error": None
            }
        ]
    },
    "processing_summary": {
        "summary": "Processing status summary",
        "description": "Overview of task processing status",
        "value": {
            "topic_id": 42,
            "queue_stats": {
                "pending": 5,
                "processing": 3,
                "completed": 127,
                "failed": 2,
                "queue_length": 8,
                "active_workers": 3,
                "average_processing_time": 45.2
            },
            "recent_tasks": {
                "total": 15,
                "last_24_hours": 15,
                "status_distribution": {
                    "completed": 10,
                    "processing": 3,
                    "pending": 2
                }
            },
            "last_updated": "2024-01-15T11:00:00Z"
        }
    },
    "websocket_message": {
        "summary": "WebSocket status update",
        "description": "Real-time task status update via WebSocket",
        "value": {
            "type": "task_status_update",
            "task_id": "task_uuid_1",
            "topic_id": 42,
            "status": "processing",
            "previous_status": "pending",
            "progress": {
                "percentage": 75.0,
                "current_operation": "存储到向量数据库",
                "current_step": 5,
                "total_steps": 6
            },
            "file_name": "document.pdf",
            "task_type": "file_embedding",
            "timestamp": "2024-01-15T10:31:30Z"
        }
    }
}

# File Upload Integration Examples
FILE_EXAMPLES = {
    "file_with_processing": {
        "summary": "File upload with automatic processing",
        "description": "Upload a file that will be automatically processed",
        "value": {
            "topic_id": 42,
            "metadata": {
                "auto_process": True,
                "processing_config": {
                    "task_types": ["file_embedding", "document_parsing"],
                    "priority": "high",
                    "chunk_size": 1000
                }
            }
        }
    },
    "signed_url_request": {
        "summary": "Request signed URL for file upload",
        "description": "Generate a secure signed URL for direct file upload to storage",
        "value": {
            "filename": "research_paper.pdf",
            "file_size": 2048000,
            "content_type": "application/pdf",
            "access_level": "private",
            "expires_in_hours": 2,
            "category": "research",
            "tags": ["ai", "machine-learning", "research"],
            "metadata": {
                "author": "Dr. Smith",
                "department": "AI Research",
                "version": "1.0"
            },
            "enable_multipart": True,
            "topic_id": 42
        }
    },
    "signed_url_response": {
        "summary": "Signed URL response",
        "description": "Response containing the signed URL and upload metadata",
        "value": {
            "file_id": "a2385d89-8824-474c-8740-8a93ef0d5469",
            "upload_url": "https://minio.example.com/files/uploads/user123/2024/01/15/file123/research_paper.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...",
            "upload_session_id": "session_a2385d89-8824-474c-8740-8a93ef0d5469",
            "expires_at": "2024-01-15T14:30:00Z",
            "multipart_upload_id": "multipart_a2385d89-8824-474c-8740-8a93ef0d5469",
            "chunk_size": 5242880,
            "max_chunks": 391
        }
    },
    "upload_completion_request": {
        "summary": "Confirm upload completion",
        "description": "Notify server that file upload has completed and trigger processing",
        "value": {
            "file_hash": "sha256:a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890",
            "actual_file_size": 2048000
        }
    },
    "upload_completion_response": {
        "summary": "Upload completion confirmation",
        "description": "Server confirmation of upload completion with processing status",
        "value": {
            "file_id": "a2385d89-8824-474c-8740-8a93ef0d5469",
            "status": "available",
            "processing_started": True,
            "task_ids": [
                "task_embedding_uuid_1",
                "task_parsing_uuid_2",
                "task_analysis_uuid_3"
            ],
            "message": "Upload completion confirmed and processing started",
            "verification_result": {
                "exists": True,
                "storage_size": 2048000,
                "size_verified": True
            }
        }
    },
    "upload_completion_error": {
        "summary": "Upload completion error",
        "description": "Error response when upload confirmation fails",
        "value": {
            "file_id": "a2385d89-8824-474c-8740-8a93ef0d5469",
            "status": "uploading",
            "processing_started": False,
            "task_ids": [],
            "message": "File was not found in storage. Upload may have failed.",
            "verification_result": {
                "exists": False,
                "error": "Object not found in bucket"
            }
        }
    }
}

# Enhanced OpenAPI Schema Customization
def enhance_openapi_schema(openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance the OpenAPI schema with additional documentation,
    examples, and metadata for the task processing system.
    """
    
    # Add task processing tag description
    if "tags" not in openapi_schema:
        openapi_schema["tags"] = []
    
    # Enhanced tag descriptions
    tag_descriptions = {
        "tasks": {
            "name": "tasks",
            "description": """
            **File Processing Tasks**
            
            Asynchronous task processing system for file embedding, parsing, and analysis.
            
            ### Features:
            - **Priority-based queue** - Tasks are processed based on priority levels
            - **Real-time updates** - WebSocket and SSE support for live status tracking
            - **Error handling** - Intelligent retry mechanisms with exponential backoff
            - **Progress tracking** - Detailed progress information with operation descriptions
            - **Multi-type processing** - Support for embedding, parsing, analysis, OCR, and thumbnails
            
            ### Task Types:
            - `file_embedding` - Generate vector embeddings for semantic search
            - `document_parsing` - Extract text, metadata, and structure
            - `content_analysis` - Keyword extraction, sentiment analysis, classification
            - `ocr_processing` - Optical character recognition for images and PDFs
            - `thumbnail_generation` - Generate preview thumbnails
            
            ### Status Flow:
            ```
            pending → processing → completed
                   ↘              ↗
                    failed → retrying
            ```
            
            ### Real-time Updates:
            - **WebSocket**: `/api/v1/tasks/ws/{topic_id}/{client_id}`
            - **Server-Sent Events**: `/api/v1/tasks/events/{topic_id}`
            """,
            "externalDocs": {
                "description": "Task Processing System Documentation",
                "url": "/docs/task-processing"
            }
        },
        "topic-files": {
            "name": "topic-files", 
            "description": """
            **Topic File Management**
            
            Enhanced file management with processing status integration.
            
            ### Features:
            - **Processing status** - Track embedding and analysis progress
            - **Unified view** - Legacy and new file systems integration
            - **Metadata enrichment** - Processing results and statistics
            - **Performance optimized** - Pagination and filtering support
            """
        },
        "file-upload": {
            "name": "file-upload",
            "description": """
            **Secure File Upload System**
            
            Advanced file upload system with signed URLs and automatic processing integration.
            
            ### Upload Workflow:
            1. **Request Signed URL** - Get secure upload URL from server
            2. **Direct Upload** - Upload file directly to storage (MinIO/S3) using signed URL
            3. **Confirm Completion** - Notify server that upload is complete
            4. **Automatic Processing** - Server triggers RAG processing pipeline
            
            ### Features:
            - **Signed URLs** - Secure direct-to-storage uploads
            - **Upload Verification** - File existence and size validation
            - **Completion Tracking** - Prevents orphaned uploads
            - **Background Monitoring** - Automatic recovery of missed uploads
            - **Processing Integration** - Seamless RAG pipeline triggering
            - **Multi-part Support** - Large file upload capabilities
            - **Metadata Management** - Rich file metadata and categorization
            
            ### Security:
            - **Time-limited URLs** - Signed URLs with configurable expiration
            - **Ownership Validation** - Users can only confirm their own uploads
            - **Storage Verification** - Server validates file existence before processing
            - **Error Handling** - Comprehensive error responses and recovery
            
            ### Status Flow:
            ```
            Request URL → Upload to Storage → Confirm Completion → Processing
                ↓               ↓                    ↓                ↓
            UPLOADING     File Stored         AVAILABLE        PROCESSING
            ```
            
            ### Orphan Recovery:
            Background monitor automatically detects and recovers uploads that were
            completed but not confirmed, ensuring no files are lost in the process.
            """,
            "externalDocs": {
                "description": "Upload Completion System Guide",
                "url": "/docs/upload-completion"
            }
        }
    }
    
    # Update existing tags or add new ones
    existing_tags = {tag["name"]: tag for tag in openapi_schema.get("tags", [])}
    
    for tag_name, tag_info in tag_descriptions.items():
        if tag_name in existing_tags:
            existing_tags[tag_name].update(tag_info)
        else:
            openapi_schema["tags"].append(tag_info)
    
    # Add examples to components
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    if "examples" not in openapi_schema["components"]:
        openapi_schema["components"]["examples"] = {}
    
    # Add task processing examples
    openapi_schema["components"]["examples"].update(TASK_EXAMPLES)
    openapi_schema["components"]["examples"].update(FILE_EXAMPLES)
    
    # Add security schemes
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    openapi_schema["components"]["securitySchemes"]["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "API key for authentication"
    }
    
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT bearer token authentication"
    }
    
    # Add global security requirements (optional)
    # openapi_schema["security"] = [
    #     {"ApiKeyAuth": []},
    #     {"BearerAuth": []}
    # ]
    
    # Add servers with descriptions
    if "servers" not in openapi_schema:
        openapi_schema["servers"] = []
    
    # Ensure we have proper server descriptions
    if not openapi_schema["servers"]:
        openapi_schema["servers"] = [
            {
                "url": "/",
                "description": "Current server"
            }
        ]
    
    # Add development and production server examples
    server_examples = [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.rag-system.com",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.rag-system.com", 
            "description": "Staging server"
        }
    ]
    
    # Only add if not already present
    existing_urls = {server.get("url") for server in openapi_schema["servers"]}
    for server in server_examples:
        if server["url"] not in existing_urls:
            openapi_schema["servers"].append(server)
    
    # Enhanced info section
    if "info" in openapi_schema:
        # Add contact and license if not present
        if "contact" not in openapi_schema["info"]:
            openapi_schema["info"]["contact"] = {
                "name": "RAG System API Support",
                "email": "api-support@rag-system.com",
                "url": "https://github.com/rag-system/api"
            }
        
        if "license" not in openapi_schema["info"]:
            openapi_schema["info"]["license"] = {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        
        # Add external documentation
        if "externalDocs" not in openapi_schema:
            openapi_schema["externalDocs"] = {
                "description": "Complete API Documentation and Guides",
                "url": "https://docs.rag-system.com"
            }
    
    # Add custom extensions
    openapi_schema["info"]["x-api-features"] = [
        "Real-time task processing",
        "WebSocket support", 
        "File processing pipeline",
        "Secure signed URL uploads",
        "Upload completion tracking",
        "Orphaned upload recovery",
        "Multi-cloud storage",
        "Health monitoring",
        "Metrics collection"
    ]
    
    return openapi_schema


# WebSocket Documentation
WEBSOCKET_DOCS = {
    "connection": """
    ### WebSocket Connection
    
    Connect to receive real-time task status updates:
    
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/tasks/ws/42/client_123');
    
    ws.onopen = function() {
        console.log('Connected to task updates');
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log('Task update:', data);
        
        switch(data.type) {
            case 'task_status_update':
                updateTaskUI(data.task_id, data.status, data.progress);
                break;
            case 'queue_stats_update':
                updateQueueStats(data.stats);
                break;
            case 'initial_status':
                initializeTaskList(data.data);
                break;
        }
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = function() {
        console.log('WebSocket connection closed');
    };
    ```
    """,
    
    "sse": """
    ### Server-Sent Events
    
    Alternative to WebSocket for real-time updates:
    
    ```javascript
    const eventSource = new EventSource('/api/v1/tasks/events/42?client_id=client_123');
    
    eventSource.addEventListener('task_update', function(event) {
        const data = JSON.parse(event.data);
        updateTaskUI(data.task_id, data.status, data.progress);
    });
    
    eventSource.addEventListener('initial_status', function(event) {
        const data = JSON.parse(event.data);
        initializeTaskList(data);
    });
    
    eventSource.addEventListener('error', function(event) {
        console.error('SSE error:', event);
    });
    ```
    """
}

# Integration Examples
INTEGRATION_EXAMPLES = {
    "complete_upload_workflow": """
    ### Complete Upload Workflow with Processing
    
    Full end-to-end file upload workflow using the new completion tracking system:
    
    ```javascript
    // Frontend Upload Implementation
    class FileUploadManager {
        async uploadFile(file, topicId) {
            try {
                // Step 1: Request signed URL
                const signedUrlResponse = await fetch('/api/v1/files/upload/signed-url', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        filename: file.name,
                        file_size: file.size,
                        content_type: file.type,
                        topic_id: topicId,
                        access_level: 'private',
                        expires_in_hours: 2
                    })
                });
                
                const signedData = await signedUrlResponse.json();
                console.log('Got signed URL:', signedData.file_id);
                
                // Step 2: Upload to storage
                const uploadResponse = await fetch(signedData.upload_url, {
                    method: 'PUT',
                    body: file,
                    headers: { 'Content-Type': file.type }
                });
                
                if (!uploadResponse.ok) {
                    throw new Error('Upload to storage failed');
                }
                
                // Step 3: Confirm completion and trigger processing
                const confirmResponse = await fetch(`/api/v1/files/${signedData.file_id}/upload/confirm`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file_hash: await this.calculateFileHash(file),
                        actual_file_size: file.size
                    })
                });
                
                const confirmData = await confirmResponse.json();
                
                return {
                    success: true,
                    file_id: signedData.file_id,
                    processing_started: confirmData.processing_started,
                    task_ids: confirmData.task_ids,
                    status: confirmData.status
                };
                
            } catch (error) {
                console.error('Upload failed:', error);
                return { success: false, error: error.message };
            }
        }
        
        async calculateFileHash(file) {
            const arrayBuffer = await file.arrayBuffer();
            const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            return 'sha256:' + hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        }
    }
    
    // Usage
    const uploader = new FileUploadManager();
    const result = await uploader.uploadFile(fileInput.files[0], 42);
    
    if (result.success) {
        console.log('Upload successful, processing started:', result.processing_started);
        if (result.task_ids.length > 0) {
            // Monitor processing progress
            monitorProcessingTasks(result.task_ids);
        }
    }
    ```
    """,
    
    "file_upload_with_processing": """
    ### Backend Processing Integration
    
    Server-side integration for automatic processing after upload confirmation:
    
    ```python
    from infrastructure.tasks.integration_example import FileProcessingIntegration
    
    async def handle_file_upload(file_data):
        integration = FileProcessingIntegration()
        await integration.initialize()
        
        # Trigger processing after upload
        result = await integration.on_file_uploaded(
            file_id=file_data["id"],
            file_path=file_data["path"],
            file_name=file_data["name"],
            file_size=file_data["size"],
            mime_type=file_data["mime_type"],
            topic_id=file_data["topic_id"],
            user_id=file_data["user_id"],
            auto_process=True,
            processing_config={
                "task_types": ["file_embedding", "document_parsing"],
                "priority": "normal"
            }
        )
        
        return {
            "file_uploaded": True,
            "processing_started": result["processing_started"],
            "task_ids": result["task_ids"]
        }
    ```
    """,
    
    "orphan_recovery_monitoring": """
    ### Orphaned Upload Recovery
    
    Monitor and automatically recover orphaned uploads:
    
    ```python
    from infrastructure.tasks.upload_monitor import UploadMonitorService
    
    # Configure upload monitor
    monitor = UploadMonitorService(
        check_interval=300,      # Check every 5 minutes
        orphan_threshold=1800,   # Consider orphaned after 30 minutes
        max_concurrent_checks=10 # Process up to 10 files simultaneously
    )
    
    # Start monitoring
    await monitor.start()
    
    # The monitor will automatically:
    # 1. Find files in 'uploading' status older than threshold
    # 2. Check if files exist in storage
    # 3. Auto-confirm uploads that exist
    # 4. Mark missing files as failed
    # 5. Trigger processing for confirmed files
    
    # Monitor runs continuously in background
    # To stop when application shuts down:
    await monitor.stop()
    ```
    """,
    
    "status_monitoring": """
    ### Status Monitoring Dashboard
    
    Create a real-time dashboard showing processing status:
    
    ```javascript
    class TaskDashboard {
        constructor(topicId, clientId) {
            this.topicId = topicId;
            this.clientId = clientId;
            this.ws = null;
            this.tasks = new Map();
            this.initWebSocket();
        }
        
        initWebSocket() {
            this.ws = new WebSocket(`ws://localhost:8000/api/v1/tasks/ws/${this.topicId}/${this.clientId}`);
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleUpdate(data);
            };
        }
        
        handleUpdate(data) {
            switch(data.type) {
                case 'task_status_update':
                    this.updateTask(data);
                    break;
                case 'queue_stats_update':
                    this.updateQueueStats(data.stats);
                    break;
            }
        }
        
        updateTask(taskData) {
            this.tasks.set(taskData.task_id, taskData);
            this.renderTask(taskData);
        }
        
        renderTask(task) {
            const element = document.getElementById(`task-${task.task_id}`);
            if (element) {
                element.querySelector('.status').textContent = task.status;
                element.querySelector('.progress-bar').style.width = `${task.progress.percentage}%`;
                element.querySelector('.operation').textContent = task.progress.current_operation;
            }
        }
    }
    
    // Initialize dashboard
    const dashboard = new TaskDashboard(42, 'client_123');
    ```
    """
}