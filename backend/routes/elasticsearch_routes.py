"""
Elasticsearch Routes - API endpoints for Elasticsearch-based log search and analytics
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from core.dependencies import get_db_session
from utils.elasticsearch_logger import ElasticsearchLoggerFactory, ElasticsearchLogger
from core.exceptions import ServiceError

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/elasticsearch", tags=["elasticsearch"])

def get_elasticsearch_logger():
    """Dependency for getting Elasticsearch logger"""
    # Get configuration from environment
    import os
    es_hosts = os.getenv('ELASTICSEARCH_HOSTS', 'http://localhost:9200').split(',')
    es_username = os.getenv('ELASTICSEARCH_USERNAME')
    es_password = os.getenv('ELASTICSEARCH_PASSWORD')
    
    try:
        return ElasticsearchLoggerFactory.create_logger(
            hosts=es_hosts,
            username=es_username,
            password=es_password
        )
    except Exception as e:
        logger.error(f"Failed to create Elasticsearch logger: {e}")
        raise HTTPException(status_code=500, detail="Elasticsearch connection failed")

# Search endpoints
@router.get("/search/logs")
async def search_logs(
    job_run_id: Optional[str] = Query(None, description="Filter by job run ID"),
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    step: Optional[str] = Query(None, description="Filter by execution step"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    query: Optional[str] = Query(None, description="Full-text search query"),
    size: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    es_logger: ElasticsearchLogger = Depends(get_elasticsearch_logger)
):
    """Search logs in Elasticsearch with advanced filtering"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format")
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format")
        
        # Perform search
        logs = es_logger.search_logs(
            job_run_id=job_run_id,
            job_id=job_id,
            level=level,
            step=step,
            start_time=start_dt,
            end_time=end_dt,
            size=size
        )
        
        return {
            "logs": logs,
            "total": len(logs),
            "filters": {
                "job_run_id": job_run_id,
                "job_id": job_id,
                "level": level,
                "step": step,
                "start_time": start_time,
                "end_time": end_time,
                "query": query
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/status-history")
async def search_status_history(
    job_run_id: Optional[str] = Query(None, description="Filter by job run ID"),
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    from_status: Optional[str] = Query(None, description="Filter by from status"),
    to_status: Optional[str] = Query(None, description="Filter by to status"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    size: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    es_logger: ElasticsearchLogger = Depends(get_elasticsearch_logger)
):
    """Search status history in Elasticsearch"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format")
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format")
        
        # Build query
        query = {"bool": {"must": []}}
        
        if job_run_id:
            query["bool"]["must"].append({"term": {"job_run_id": job_run_id}})
        if job_id:
            query["bool"]["must"].append({"term": {"job_id": job_id}})
        if from_status:
            query["bool"]["must"].append({"term": {"from_status": from_status}})
        if to_status:
            query["bool"]["must"].append({"term": {"to_status": to_status}})
        if start_dt or end_dt:
            time_range = {}
            if start_dt:
                time_range["gte"] = start_dt.isoformat()
            if end_dt:
                time_range["lte"] = end_dt.isoformat()
            query["bool"]["must"].append({"range": {"timestamp": time_range}})
        
        if not query["bool"]["must"]:
            query = {"match_all": {}}
        
        # Determine index pattern
        if job_run_id:
            index_pattern = f"job-logs-status-history-{job_run_id}-*"
        else:
            index_pattern = "job-logs-status-history-*"
        
        response = es_logger.es.search(
            index=index_pattern,
            body={
                "query": query,
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": size
            }
        )
        
        results = [hit["_source"] for hit in response["hits"]["hits"]]
        
        return {
            "status_history": results,
            "total": len(results),
            "filters": {
                "job_run_id": job_run_id,
                "job_id": job_id,
                "from_status": from_status,
                "to_status": to_status,
                "start_time": start_time,
                "end_time": end_time
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching status history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@router.get("/analytics/log-statistics")
async def get_log_statistics(
    job_run_id: Optional[str] = Query(None, description="Filter by job run ID"),
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    es_logger: ElasticsearchLogger = Depends(get_elasticsearch_logger)
):
    """Get log statistics from Elasticsearch"""
    try:
        # Parse time parameters
        start_dt = None
        end_dt = None
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_time format")
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_time format")
        
        stats = es_logger.get_log_statistics(
            job_run_id=job_run_id,
            job_id=job_id,
            start_time=start_dt,
            end_time=end_dt
        )
        
        return {
            "statistics": stats,
            "filters": {
                "job_run_id": job_run_id,
                "job_id": job_id,
                "start_time": start_time,
                "end_time": end_time
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting log statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/error-analysis")
async def get_error_analysis(
    job_run_id: Optional[str] = Query(None, description="Filter by job run ID"),
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    es_logger: ElasticsearchLogger = Depends(get_elasticsearch_logger)
):
    """Get error analysis from Elasticsearch"""
    try:
        from datetime import datetime, timedelta
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Search for error logs
        error_logs = es_logger.search_logs(
            job_run_id=job_run_id,
            job_id=job_id,
            level="ERROR",
            start_time=start_time,
            end_time=end_time,
            size=1000
        )
        
        # Analyze errors
        error_counts = {}
        error_codes = {}
        job_error_counts = {}
        
        for log in error_logs:
            # Count by error code
            error_code = log.get('error_code', 'UNKNOWN')
            error_codes[error_code] = error_codes.get(error_code, 0) + 1
            
            # Count by job
            job_name = log.get('job_name', 'Unknown')
            job_error_counts[job_name] = job_error_counts.get(job_name, 0) + 1
            
            # Count by step
            step = log.get('step', 'Unknown')
            if step not in error_counts:
                error_counts[step] = 0
            error_counts[step] += 1
        
        return {
            "analysis": {
                "total_errors": len(error_logs),
                "period_days": days,
                "error_counts_by_step": error_counts,
                "error_counts_by_code": error_codes,
                "error_counts_by_job": job_error_counts,
                "recent_errors": error_logs[:10]  # Last 10 errors
            },
            "filters": {
                "job_run_id": job_run_id,
                "job_id": job_id,
                "days": days
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting error analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/performance-metrics")
async def get_performance_metrics(
    job_run_id: Optional[str] = Query(None, description="Filter by job run ID"),
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    es_logger: ElasticsearchLogger = Depends(get_elasticsearch_logger)
):
    """Get performance metrics from Elasticsearch"""
    try:
        from datetime import datetime, timedelta
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Search for logs with duration
        logs_with_duration = es_logger.search_logs(
            job_run_id=job_run_id,
            job_id=job_id,
            start_time=start_time,
            end_time=end_time,
            size=1000
        )
        
        # Calculate performance metrics
        step_durations = {}
        total_duration = 0
        step_counts = {}
        
        for log in logs_with_duration:
            duration_ms = log.get('duration_ms')
            step = log.get('step')
            
            if duration_ms and step:
                if step not in step_durations:
                    step_durations[step] = []
                step_durations[step].append(duration_ms)
                total_duration += duration_ms
                
                step_counts[step] = step_counts.get(step, 0) + 1
        
        # Calculate averages
        step_averages = {}
        for step, durations in step_durations.items():
            step_averages[step] = sum(durations) / len(durations)
        
        return {
            "performance_metrics": {
                "total_duration_ms": total_duration,
                "step_average_durations": step_averages,
                "step_execution_counts": step_counts,
                "total_logs_analyzed": len(logs_with_duration),
                "period_days": days
            },
            "filters": {
                "job_run_id": job_run_id,
                "job_id": job_id,
                "days": days
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Management endpoints
@router.get("/health")
async def elasticsearch_health(
    es_logger: ElasticsearchLogger = Depends(get_elasticsearch_logger)
):
    """Check Elasticsearch health"""
    try:
        # Test connection
        health = es_logger.es.cluster.health()
        
        return {
            "status": "healthy",
            "cluster_health": health,
            "connection": "ok"
        }
        
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "connection": "failed"
        }

@router.get("/indices")
async def list_indices(
    es_logger: ElasticsearchLogger = Depends(get_elasticsearch_logger)
):
    """List Elasticsearch indices"""
    try:
        indices = es_logger.es.indices.get_alias(index="job-logs-*")
        
        return {
            "indices": list(indices.keys()),
            "total_indices": len(indices)
        }
        
    except Exception as e:
        logger.error(f"Failed to list indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/indices/{index_pattern}")
async def delete_indices(
    index_pattern: str,
    es_logger: ElasticsearchLogger = Depends(get_elasticsearch_logger)
):
    """Delete Elasticsearch indices"""
    try:
        # Safety check - only allow deletion of job-logs indices
        if not index_pattern.startswith("job-logs-"):
            raise HTTPException(status_code=400, detail="Can only delete job-logs indices")
        
        result = es_logger.es.indices.delete(index=index_pattern)
        
        return {
            "message": f"Successfully deleted indices matching pattern: {index_pattern}",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to delete indices: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 