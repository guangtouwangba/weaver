# Celery Integration for Research Agent RAG

This document explains the Celery integration that makes job execution truly asynchronous in the Research Agent RAG system.

## Overview

The Celery integration transforms the research job execution from synchronous to asynchronous, providing:

- **Immediate Response**: API calls return instantly with a task ID
- **Real-time Progress**: Track job progress via task status endpoints
- **Scalable Workers**: Multiple worker processes can handle jobs concurrently
- **Retry Logic**: Automatic retry on failures with exponential backoff
- **Task Monitoring**: Built-in monitoring via Flower web interface

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Celery        │
│                 │    │   Backend       │    │   Workers       │
│                 │    │                 │    │                 │
│ Trigger Job ────┼───►│ /trigger POST   │    │                 │
│                 │    │ Returns task_id │    │                 │
│                 │    │                 │    │                 │
│ Check Status ───┼───►│ /tasks/{id}     │    │                 │
│                 │    │ Returns progress│    │                 │
│                 │    │                 │    │                 │
│                 │    │ Queue Task ─────┼───►│ Execute Job     │
│                 │    │                 │    │ Update Progress │
│                 │    │                 │    │ Store Results   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                ▲                       │
                                │                       │
                                │    ┌─────────────────┐│
                                └────│   Redis         ││
                                     │   Message       ││
                                     │   Broker        ││
                                     └─────────────────┘│
                                      ┌─────────────────┘
                                      │
                                ┌─────▼─────────────────┐
                                │   PostgreSQL          │
                                │   Database            │
                                │   (Job Runs &         │
                                │    Progress)          │
                                └───────────────────────┘
```

## Components

### 1. Celery App Configuration (`celery_app.py`)
- Configured with Redis as message broker and result backend
- Task routing for different queue types
- Serialization and retry settings from Config class

### 2. Research Tasks (`tasks/research_tasks.py`)
- `execute_research_job`: Main async task for job execution
- `process_papers`: Sub-task for paper processing
- `health_check`: System health verification
- `cleanup_old_tasks`: Maintenance task

### 3. Task Utilities (`tasks/task_utils.py`)
- `TaskRetryPolicy`: Configurable retry logic with exponential backoff
- `TaskProgressManager`: Progress tracking with time estimation
- Error handling and resource cleanup utilities

### 4. Database Integration
- New `task_id` field in `job_runs` table
- Progress tracking fields: `progress_percentage`, `current_step`
- Manual trigger support: `manual_trigger`, `user_params`

### 5. API Endpoints
- `POST /api/cronjobs/{id}/trigger`: Trigger job (returns immediately)
- `GET /api/cronjobs/tasks/{task_id}/status`: Get task status
- `GET /api/cronjobs/tasks/{task_id}/progress`: Get detailed progress
- `POST /api/cronjobs/tasks/{task_id}/cancel`: Cancel running task
- `GET /api/cronjobs/tasks/health-check`: Health check endpoint

## Configuration

### Environment Variables

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://:password@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:password@localhost:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_TASK_ACKS_LATE=true
CELERY_RESULT_EXPIRES=3600
CELERY_TASK_DEFAULT_RETRY_DELAY=60
CELERY_TASK_MAX_RETRIES=3
```

### Configuration Class Updates

The `Config` class now includes all Celery settings with sensible defaults that automatically derive from Redis configuration.

## Development Setup

### Option 1: Using the Development Script

```bash
# Start all services (Redis, Celery workers, FastAPI)
./start_dev.sh
```

This script:
- Starts Redis server
- Starts Celery worker and beat scheduler
- Starts Flower monitoring interface
- Runs database migrations
- Starts FastAPI server with auto-reload

### Option 2: Manual Setup

```bash
# Start Redis
redis-server --daemonize yes

# Start Celery worker
python manage_celery.py start --workers 2 --concurrency 2 --flower

# Start FastAPI server
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Docker Compose

```bash
# Start middleware services (Redis, PostgreSQL, etc.)
docker-compose -f infra/docker/docker-compose.middleware.yml up -d

# Start application services (includes Celery workers)
docker-compose -f infra/docker/docker-compose.yml up -d
```

## Production Deployment

### Docker Services

The docker-compose.yml includes:

- **celery-worker**: Main worker for research tasks
- **celery-beat**: Scheduler for periodic tasks
- **celery-flower**: Monitoring interface (optional)

### Scaling Workers

```bash
# Scale workers horizontally
docker-compose up -d --scale celery-worker=4

# Or manually add workers
docker run -d --name worker-2 your-app:latest \
  celery -A celery_app worker --loglevel=info --concurrency=4
```

### Monitoring

#### Flower Web Interface
- URL: `http://localhost:5555`
- Real-time task monitoring
- Worker statistics
- Task history and results

#### Health Check Endpoint
```bash
curl http://localhost:8000/api/cronjobs/tasks/health-check
```

#### Management Commands
```bash
# Check system status
python manage_celery.py status

# Run health check
python manage_celery.py health

# Monitor processes
python manage_celery.py monitor
```

## API Usage Examples

### 1. Trigger a Job

```bash
curl -X POST "http://localhost:8000/api/cronjobs/{job_id}/trigger" \
  -H "Content-Type: application/json" \
  -d '{"force_reprocess": false}'
```

Response:
```json
{
  "job_run_id": "pending",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PENDING",
  "message": "Job execution queued successfully. Task ID: a1b2c3d4-..."
}
```

### 2. Check Task Status

```bash
curl "http://localhost:8000/api/cronjobs/tasks/{task_id}/status"
```

Response:
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PROGRESS",
  "progress": 60,
  "description": "Processing 15 papers...",
  "current": 3,
  "total": 5,
  "job_run_id": "uuid-of-job-run",
  "elapsed_time": 45.2,
  "estimated_remaining": 30.1
}
```

### 3. Get Detailed Progress

```bash
curl "http://localhost:8000/api/cronjobs/tasks/{task_id}/progress"
```

Response includes database-stored progress plus real-time Celery task state.

### 4. Cancel a Task

```bash
curl -X POST "http://localhost:8000/api/cronjobs/tasks/{task_id}/cancel"
```

## Error Handling and Retries

### Retry Policy

Tasks automatically retry on failures with:
- **Exponential backoff**: Base delay × (factor ^ retry_count)
- **Maximum retries**: Configurable (default: 3)
- **Smart retry logic**: Won't retry validation errors or authentication failures

### Error States

- `PENDING`: Task queued but not started
- `PROGRESS`: Task running with progress updates
- `RETRY`: Task failed, will retry
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed permanently
- `REVOKED`: Task cancelled

### Database Integration

All task states are synchronized with the database:
- Job runs track task_id for correlation
- Progress updates stored in database
- Error messages and logs preserved
- Failed tasks marked appropriately

## Performance Considerations

### Worker Configuration

```python
# Recommended production settings
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Prevent memory issues
CELERY_TASK_ACKS_LATE = True          # Ensure reliability
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Prevent memory leaks
```

### Queue Optimization

- **research**: Heavy computation tasks
- **processing**: Paper processing subtasks
- Separate queues allow different scaling strategies

### Memory Management

- Workers restart after processing 1000 tasks
- Task results expire after 1 hour
- Old job runs cleaned up automatically

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Check configuration
   echo $CELERY_BROKER_URL
   ```

2. **No Workers Available**
   ```bash
   # Check worker status
   celery -A celery_app inspect active
   
   # Start workers manually
   python manage_celery.py start --workers 2
   ```

3. **Tasks Stuck in PENDING**
   - Workers not running or crashed
   - Redis connection issues
   - Task routing problems

4. **High Memory Usage**
   - Increase `CELERY_WORKER_MAX_TASKS_PER_CHILD`
   - Reduce `CELERY_WORKER_PREFETCH_MULTIPLIER`
   - Scale workers horizontally instead of vertically

### Debugging Commands

```bash
# List active tasks
celery -A celery_app inspect active

# List scheduled tasks
celery -A celery_app inspect scheduled

# List reserved tasks
celery -A celery_app inspect reserved

# Show worker statistics
celery -A celery_app inspect stats

# Purge all tasks
celery -A celery_app purge
```

## Frontend Integration

The frontend should be updated to:

1. **Handle Immediate Response**: Store task_id from trigger response
2. **Poll Task Status**: Implement periodic status checking
3. **Show Progress**: Display real-time progress updates
4. **Handle Task States**: Show appropriate UI for each task state
5. **Allow Cancellation**: Provide cancel button for running tasks

### Example Frontend Flow

```javascript
// 1. Trigger job
const response = await fetch('/api/cronjobs/123/trigger', {
  method: 'POST',
  body: JSON.stringify({force_reprocess: false})
});
const {task_id} = await response.json();

// 2. Poll status
const pollStatus = async () => {
  const status = await fetch(`/api/cronjobs/tasks/${task_id}/status`);
  const data = await status.json();
  
  updateProgressBar(data.progress);
  updateStatusText(data.description);
  
  if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
    clearInterval(polling);
  }
};

// 3. Start polling
const polling = setInterval(pollStatus, 2000);
```

## Migration from Synchronous System

The integration maintains backward compatibility:

1. **Database**: New fields have defaults, existing data unaffected
2. **API**: Old endpoints continue to work (though not recommended)
3. **Services**: Original service methods preserved alongside new async methods

### Migration Steps

1. Deploy Celery infrastructure (Redis, workers)
2. Update frontend to use new async endpoints
3. Monitor system performance and adjust worker scaling
4. Remove old synchronous endpoints after validation

This completes the Celery integration, providing a robust, scalable, and monitorable asynchronous task execution system for the Research Agent RAG backend.