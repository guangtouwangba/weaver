"""
Job Log Routes - API endpoints for job logging and monitoring with real-time support
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Body, WebSocket
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

from core.dependencies import get_db_session
from services.job_log_service import JobLogService
from models.schemas.job_log import (
    LogSearchRequest, LogSearchResponse, LogSearchFilters,
    RealTimeLogRequest, RealTimeLogResponse, JobLogResponse,
    LogStatistics, ElasticsearchQueryRequest, ElasticsearchQueryResponse
)
from utils.websocket_manager import log_streaming_service
from core.exceptions import NotFoundError, ServiceError

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api", tags=["job-logs"])

def get_job_log_service(db_session: Session = Depends(get_db_session)) -> JobLogService:
    """Dependency for getting job log service"""
    return JobLogService(db_session)

# Job Run Logs
@router.get("/job-runs/{job_run_id}/logs")
async def get_job_run_logs(
    job_run_id: str,
    level: Optional[str] = Query(None, description="Filter by log level"),
    step: Optional[str] = Query(None, description="Filter by execution step"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Get logs for a specific job run"""
    try:
        logs = service.get_job_run_logs(job_run_id, level, step, limit, offset)
        return {
            "job_run_id": job_run_id,
            "logs": logs,
            "total": len(logs),
            "limit": limit,
            "offset": offset
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job-runs/{job_run_id}/logs/realtime")
async def get_real_time_logs(
    job_run_id: str,
    last_log_id: Optional[str] = Query(None, description="Last seen log ID for incremental updates"),
    limit: int = Query(50, ge=1, le=200, description="Number of logs to return"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Get real-time logs for monitoring"""
    try:
        logs = service.get_real_time_logs(job_run_id, last_log_id, limit)
        return {
            "job_run_id": job_run_id,
            "logs": logs,
            "total": len(logs),
            "last_log_id": logs[-1]["id"] if logs else last_log_id
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Job Logs (across all runs)
@router.get("/jobs/{job_id}/logs")
async def get_job_logs(
    job_id: str,
    level: Optional[str] = Query(None, description="Filter by log level"),
    step: Optional[str] = Query(None, description="Filter by execution step"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Get logs for all runs of a specific job"""
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        logs = service.get_job_logs(job_id, level, step, start_dt, end_dt, limit, offset)
        return {
            "job_id": job_id,
            "logs": logs,
            "total": len(logs),
            "limit": limit,
            "offset": offset
        }
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error Logs
@router.get("/logs/errors")
async def get_error_logs(
    job_run_id: Optional[str] = Query(None, description="Filter by job run ID"),
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Get error logs for recent runs"""
    try:
        logs = service.get_error_logs(job_run_id, job_id, days)
        return {
            "error_logs": logs,
            "total": len(logs),
            "period_days": days
        }
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Log Statistics
@router.get("/logs/statistics")
async def get_log_statistics(
    job_run_id: Optional[str] = Query(None, description="Filter by job run ID"),
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Get log statistics"""
    try:
        stats = service.get_log_statistics(job_run_id, job_id, days)
        return stats
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Status History
@router.get("/job-runs/{job_run_id}/status-history")
async def get_status_history(
    job_run_id: str,
    service: JobLogService = Depends(get_job_log_service)
):
    """Get status history for a job run"""
    try:
        history = service.get_status_history(job_run_id)
        return {
            "job_run_id": job_run_id,
            "status_history": history,
            "total": len(history)
        }
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Metrics
@router.get("/job-runs/{job_run_id}/metrics")
async def get_job_run_metrics(
    job_run_id: str,
    metric_name: Optional[str] = Query(None, description="Filter by metric name"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Get metrics for a job run"""
    try:
        metrics = service.get_metrics(job_run_id, metric_name, metric_type)
        return {
            "job_run_id": job_run_id,
            "metrics": metrics,
            "total": len(metrics)
        }
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job-runs/{job_run_id}/metrics/summary")
async def get_metric_summary(
    job_run_id: str,
    service: JobLogService = Depends(get_job_log_service)
):
    """Get metric summary for a job run"""
    try:
        summary = service.get_metric_summary(job_run_id)
        return {
            "job_run_id": job_run_id,
            "metrics_summary": summary
        }
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/metrics")
async def get_job_metrics(
    job_id: str,
    metric_name: Optional[str] = Query(None, description="Filter by metric name"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Get metrics for all runs of a specific job"""
    try:
        metrics = service.get_job_metrics(job_id, metric_name, days)
        return {
            "job_id": job_id,
            "metrics": metrics,
            "total": len(metrics),
            "period_days": days
        }
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Job Run Summary
@router.get("/job-runs/{job_run_id}/summary")
async def get_job_run_summary(
    job_run_id: str,
    service: JobLogService = Depends(get_job_log_service)
):
    """Get comprehensive summary for a job run"""
    try:
        summary = service.get_job_run_summary(job_run_id)
        return summary
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Maintenance
@router.post("/maintenance/cleanup")
async def cleanup_old_logs(
    days: int = Query(90, ge=1, le=365, description="Delete logs older than this many days"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Clean up old logs to prevent database bloat"""
    try:
        deleted_count = service.cleanup_old_logs(days)
        return {
            "message": f"Successfully cleaned up {deleted_count} old log entries",
            "deleted_count": deleted_count,
            "cutoff_days": days
        }
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

# New Enhanced Real-time and Search API Endpoints

@router.post("/search", response_model=LogSearchResponse)
async def search_logs(
    search_request: LogSearchRequest,
    service: JobLogService = Depends(get_job_log_service)
):
    """Advanced log search with Elasticsearch support"""
    try:
        return service.search_logs_elasticsearch(
            filters=search_request.filters,
            skip=search_request.skip,
            limit=search_request.limit,
            sort_by=search_request.sort_by,
            sort_order=search_request.sort_order
        )
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cronjobs/{job_id}/logs", response_model=LogSearchResponse)
async def get_cronjob_logs(
    job_id: str,
    level: Optional[str] = Query(None, description="Filter by log level"),
    step: Optional[str] = Query(None, description="Filter by execution step"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    search: Optional[str] = Query(None, description="Text search in log messages"),
    skip: int = Query(0, ge=0, description="Number of logs to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Get logs for a specific cronjob with advanced filtering - This is the main endpoint requested"""
    try:
        # Parse dates
        parsed_start_time = None
        parsed_end_time = None
        if start_time:
            try:
                parsed_start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format")
        if end_time:
            try:
                parsed_end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format")
        
        filters = LogSearchFilters(
            job_id=job_id,
            level=level,
            step=step,
            start_time=parsed_start_time,
            end_time=parsed_end_time,
            search=search
        )
        
        return service.search_logs_elasticsearch(
            filters=filters,
            skip=skip,
            limit=limit
        )
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cronjobs/{job_id}/logs/realtime")
async def get_cronjob_realtime_logs(
    job_id: str,
    since_timestamp: Optional[str] = Query(None, description="Get logs since this timestamp"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(50, ge=1, le=200, description="Number of logs to return"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Get real-time logs for a cronjob"""
    try:
        # Parse timestamp
        parsed_since = None
        if since_timestamp:
            try:
                parsed_since = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid since_timestamp format")
        
        filters = LogSearchFilters(
            job_id=job_id,
            level=level,
            start_time=parsed_since
        )
        
        result = service.search_logs_elasticsearch(
            filters=filters,
            skip=0,
            limit=limit,
            sort_by="timestamp",
            sort_order="desc"
        )
        
        return RealTimeLogResponse(
            job_run_id="",  # For job-level logs
            logs=result.logs,
            last_log_id=result.logs[0].id if result.logs else None,
            has_more=result.has_more,
            poll_interval=2000  # 2 seconds for job-level logs
        )
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job-runs/{job_run_id}/logs/realtime-enhanced")
async def get_enhanced_realtime_logs(
    job_run_id: str,
    since_timestamp: Optional[str] = Query(None, description="Get logs since this timestamp"),
    last_log_id: Optional[str] = Query(None, description="Last seen log ID"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(50, ge=1, le=200, description="Number of logs to return"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Enhanced real-time logs with better filtering"""
    try:
        # Parse timestamp
        parsed_since = None
        if since_timestamp:
            try:
                parsed_since = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid since_timestamp format")
        
        filters = LogSearchFilters(
            job_run_id=job_run_id,
            level=level,
            start_time=parsed_since
        )
        
        result = service.search_logs_elasticsearch(
            filters=filters,
            skip=0,
            limit=limit,
            sort_by="timestamp",
            sort_order="desc"
        )
        
        return RealTimeLogResponse(
            job_run_id=job_run_id,
            logs=result.logs,
            last_log_id=result.logs[0].id if result.logs else last_log_id,
            has_more=result.has_more,
            poll_interval=1000  # 1 second for job run logs
        )
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aggregations")
async def get_log_aggregations(
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    job_run_id: Optional[str] = Query(None, description="Filter by job run ID"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Get log aggregations and statistics"""
    try:
        # Parse dates
        parsed_start_time = None
        parsed_end_time = None
        if start_time:
            try:
                parsed_start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format")
        if end_time:
            try:
                parsed_end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format")
        
        filters = LogSearchFilters(
            job_id=job_id,
            job_run_id=job_run_id,
            start_time=parsed_start_time,
            end_time=parsed_end_time
        )
        
        return service.get_log_aggregations(filters)
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/elasticsearch/query")
async def elasticsearch_query(
    query_request: ElasticsearchQueryRequest,
    service: JobLogService = Depends(get_job_log_service)
):
    """Direct Elasticsearch query for advanced users"""
    try:
        if not service.es_logger:
            raise HTTPException(status_code=503, detail="Elasticsearch not available")
        
        # Build index pattern
        index_pattern = f"{service.es_logger.index_prefix}-job-logs-*"
        if query_request.job_run_id:
            index_pattern = f"{service.es_logger.index_prefix}-job-logs-{query_request.job_run_id}-*"
        
        # Execute query
        response = service.es_logger.es.search(
            index=index_pattern,
            body={
                "query": query_request.query,
                "from": query_request.from_,
                "size": query_request.size,
                "sort": query_request.sort or [{"timestamp": {"order": "desc"}}]
            }
        )
        
        return ElasticsearchQueryResponse(
            hits=[hit["_source"] for hit in response["hits"]["hits"]],
            total=response["hits"]["total"]["value"],
            took=response["took"],
            aggregations=response.get("aggregations")
        )
    except Exception as e:
        logger.error(f"Elasticsearch query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job-runs/{job_run_id}/logs/stream")
async def stream_job_run_logs(
    job_run_id: str,
    level: Optional[str] = Query(None, description="Filter by log level"),
    service: JobLogService = Depends(get_job_log_service)
):
    """Stream logs using Server-Sent Events"""
    async def log_streamer():
        import asyncio
        last_timestamp = None
        
        while True:
            try:
                filters = LogSearchFilters(
                    job_run_id=job_run_id,
                    level=level,
                    start_time=last_timestamp
                )
                
                result = service.search_logs_elasticsearch(
                    filters=filters,
                    skip=0,
                    limit=50,
                    sort_by="timestamp",
                    sort_order="asc"
                )
                
                for log in result.logs:
                    yield f"data: {json.dumps(log.dict())}\n\n"
                    last_timestamp = log.timestamp
                
                # Sleep for a short interval before checking for new logs
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error streaming logs: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(
        log_streamer(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# WebSocket Endpoints for Real-time Log Streaming

@router.websocket("/job-runs/{job_run_id}/logs/ws")
async def websocket_job_run_logs(websocket: WebSocket, job_run_id: str):
    """WebSocket endpoint for real-time job run log streaming"""
    await log_streaming_service.handle_websocket_connection(websocket, job_run_id)

@router.websocket("/cronjobs/{job_id}/logs/ws")
async def websocket_cronjob_logs(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time cronjob log streaming"""
    # For job-level streaming, we'll use the job_id as the identifier
    await log_streaming_service.handle_websocket_connection(websocket, f"job_{job_id}") 