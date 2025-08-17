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
    "file_upload_with_processing": """
    ### File Upload with Automatic Processing
    
    When a file is uploaded, automatically trigger processing tasks:
    
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