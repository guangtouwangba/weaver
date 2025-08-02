"""
Job Log Service - High-level service for job logging and monitoring with Elasticsearch support
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from database.models import JobLog, JobStatusHistory, JobMetrics, JobRun
from repositories.job_log_repository import JobLogRepository, JobStatusHistoryRepository, JobMetricsRepository
from utils.job_logger import JobLogger, JobLoggerFactory
from utils.elasticsearch_logger import ElasticsearchLoggerFactory
try:
    from elasticsearch_config.elasticsearch_config import elasticsearch_config
except ImportError:
    # Fallback configuration if elasticsearch_config is not available
    class DummyElasticsearchConfig:
        def is_configured(self):
            return False
        def get_config_dict(self):
            return {'enabled': False}
    elasticsearch_config = DummyElasticsearchConfig()
from models.schemas.job_log import LogSearchFilters, LogSearchResponse, JobLogResponse
from core.exceptions import NotFoundError, ServiceError

logger = logging.getLogger(__name__)

class JobLogService:
    """Service for managing job logs and metrics"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.log_repo = JobLogRepository(db_session)
        self.status_repo = JobStatusHistoryRepository(db_session)
        self.metrics_repo = JobMetricsRepository(db_session)
        
        # Initialize Elasticsearch logger if configured
        self.es_logger = None
        if elasticsearch_config.is_configured():
            try:
                es_logger = ElasticsearchLoggerFactory.create_logger(
                    hosts=elasticsearch_config.hosts,
                    username=elasticsearch_config.username,
                    password=elasticsearch_config.password,
                    index_prefix=elasticsearch_config.index_prefix
                )
                # Only set es_logger if Elasticsearch client is actually available
                if es_logger.es is not None:
                    self.es_logger = es_logger
                    logger.info("Elasticsearch logger initialized successfully")
                else:
                    logger.warning("Elasticsearch logger created but client is None - using database fallback")
                    self.es_logger = None
            except Exception as e:
                logger.warning(f"Failed to initialize Elasticsearch logger: {e}")
                self.es_logger = None
    
    def create_logger(self, job_run_id: str) -> JobLogger:
        """Create a job logger for a specific job run"""
        return JobLoggerFactory.create_logger(job_run_id, self.db_session)
    
    def get_job_run_logs(self, job_run_id: str,
                         level: Optional[str] = None,
                         step: Optional[str] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[Dict[str, Any]]:
        """Get logs for a specific job run"""
        try:
            logs = self.log_repo.get_logs_by_job_run(job_run_id, level, step, limit, offset)
            return [self._log_to_dict(log) for log in logs]
        except Exception as e:
            logger.error(f"Error getting logs for job run {job_run_id}: {e}")
            raise ServiceError(f"Failed to get logs: {str(e)}")
    
    def get_job_logs(self, job_id: str,
                     level: Optional[str] = None,
                     step: Optional[str] = None,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None,
                     limit: int = 100,
                     offset: int = 0) -> List[Dict[str, Any]]:
        """Get logs for all runs of a specific job"""
        try:
            logs = self.log_repo.get_logs_by_job(job_id, level, step, start_date, end_date, limit, offset)
            return [self._log_to_dict(log) for log in logs]
        except Exception as e:
            logger.error(f"Error getting logs for job {job_id}: {e}")
            raise ServiceError(f"Failed to get logs: {str(e)}")
    
    def get_error_logs(self, job_run_id: Optional[str] = None,
                      job_id: Optional[str] = None,
                      days: int = 7) -> List[Dict[str, Any]]:
        """Get error logs for recent runs"""
        try:
            logs = self.log_repo.get_error_logs(job_run_id, job_id, days)
            return [self._log_to_dict(log) for log in logs]
        except Exception as e:
            logger.error(f"Error getting error logs: {e}")
            raise ServiceError(f"Failed to get error logs: {str(e)}")
    
    def get_log_statistics(self, job_run_id: Optional[str] = None,
                          job_id: Optional[str] = None,
                          days: int = 30) -> Dict[str, Any]:
        """Get log statistics"""
        try:
            return self.log_repo.get_log_statistics(job_run_id, job_id, days)
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            raise ServiceError(f"Failed to get log statistics: {str(e)}")
    
    def get_status_history(self, job_run_id: str) -> List[Dict[str, Any]]:
        """Get status history for a job run"""
        try:
            history = self.status_repo.get_status_history(job_run_id)
            return [self._status_history_to_dict(entry) for entry in history]
        except Exception as e:
            logger.error(f"Error getting status history for job run {job_run_id}: {e}")
            raise ServiceError(f"Failed to get status history: {str(e)}")
    
    def get_metrics(self, job_run_id: str,
                   metric_name: Optional[str] = None,
                   metric_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get metrics for a job run"""
        try:
            metrics = self.metrics_repo.get_metrics(job_run_id, metric_name, metric_type)
            return [self._metric_to_dict(metric) for metric in metrics]
        except Exception as e:
            logger.error(f"Error getting metrics for job run {job_run_id}: {e}")
            raise ServiceError(f"Failed to get metrics: {str(e)}")
    
    def get_metric_summary(self, job_run_id: str) -> Dict[str, Any]:
        """Get metric summary for a job run"""
        try:
            return self.metrics_repo.get_metric_summary(job_run_id)
        except Exception as e:
            logger.error(f"Error getting metric summary for job run {job_run_id}: {e}")
            raise ServiceError(f"Failed to get metric summary: {str(e)}")
    
    def get_job_metrics(self, job_id: str,
                       metric_name: Optional[str] = None,
                       days: int = 30) -> List[Dict[str, Any]]:
        """Get metrics for all runs of a specific job"""
        try:
            metrics = self.metrics_repo.get_metrics_by_job(job_id, metric_name, days)
            return [self._metric_to_dict(metric) for metric in metrics]
        except Exception as e:
            logger.error(f"Error getting metrics for job {job_id}: {e}")
            raise ServiceError(f"Failed to get job metrics: {str(e)}")
    
    def get_real_time_logs(self, job_run_id: str, 
                          last_log_id: Optional[str] = None,
                          limit: int = 50) -> List[Dict[str, Any]]:
        """Get real-time logs for monitoring"""
        try:
            query = self.db_session.query(JobLog).filter(JobLog.job_run_id == job_run_id)
            
            if last_log_id:
                # Get logs after the last seen log
                last_log = self.db_session.query(JobLog).filter(JobLog.id == last_log_id).first()
                if last_log:
                    query = query.filter(JobLog.timestamp > last_log.timestamp)
            
            logs = query.order_by(JobLog.timestamp.desc()).limit(limit).all()
            return [self._log_to_dict(log) for log in logs]
            
        except Exception as e:
            logger.error(f"Error getting real-time logs for job run {job_run_id}: {e}")
            raise ServiceError(f"Failed to get real-time logs: {str(e)}")
    
    def get_job_run_summary(self, job_run_id: str) -> Dict[str, Any]:
        """Get comprehensive summary for a job run"""
        try:
            # Get job run
            job_run = self.db_session.query(JobRun).filter(JobRun.id == job_run_id).first()
            if not job_run:
                raise NotFoundError(f"JobRun {job_run_id} not found")
            
            # Get latest logs
            logs = self.log_repo.get_logs_by_job_run(job_run_id, limit=10)
            
            # Get status history
            status_history = self.status_repo.get_status_history(job_run_id)
            
            # Get metrics summary
            metrics_summary = self.metrics_repo.get_metric_summary(job_run_id)
            
            # Get log statistics
            log_stats = self.log_repo.get_log_statistics(job_run_id, days=1)
            
            return {
                'job_run': {
                    'id': str(job_run.id),
                    'job_id': str(job_run.job_id),
                    'status': job_run.status,
                    'started_at': job_run.started_at.isoformat() if job_run.started_at else None,
                    'completed_at': job_run.completed_at.isoformat() if job_run.completed_at else None,
                    'progress_percentage': job_run.progress_percentage,
                    'current_step': job_run.current_step,
                    'papers_found': job_run.papers_found,
                    'papers_processed': job_run.papers_processed,
                    'papers_embedded': job_run.papers_embedded,
                    'embedding_errors': job_run.embedding_errors,
                    'vector_db_errors': job_run.vector_db_errors,
                    'error_message': job_run.error_message
                },
                'logs': [self._log_to_dict(log) for log in logs],
                'status_history': [self._status_history_to_dict(entry) for entry in status_history],
                'metrics': metrics_summary,
                'log_statistics': log_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting job run summary for {job_run_id}: {e}")
            raise ServiceError(f"Failed to get job run summary: {str(e)}")
    
    def cleanup_old_logs(self, days: int = 90) -> int:
        """Clean up old logs to prevent database bloat"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Delete old logs
            deleted_logs = self.db_session.query(JobLog)\
                .filter(JobLog.timestamp < cutoff_date).delete()
            
            # Delete old status history
            deleted_status = self.db_session.query(JobStatusHistory)\
                .filter(JobStatusHistory.timestamp < cutoff_date).delete()
            
            # Delete old metrics
            deleted_metrics = self.db_session.query(JobMetrics)\
                .filter(JobMetrics.timestamp < cutoff_date).delete()
            
            self.db_session.commit()
            
            logger.info(f"Cleaned up {deleted_logs} logs, {deleted_status} status entries, {deleted_metrics} metrics")
            return deleted_logs + deleted_status + deleted_metrics
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            self.db_session.rollback()
            raise ServiceError(f"Failed to cleanup old logs: {str(e)}")
    
    def _log_to_dict(self, log: JobLog) -> Dict[str, Any]:
        """Convert log object to dictionary"""
        return {
            'id': str(log.id),
            'job_run_id': str(log.job_run_id),
            'timestamp': log.timestamp.isoformat(),
            'level': log.level,
            'message': log.message,
            'details': log.details,
            'step': log.step,
            'paper_id': log.paper_id,
            'error_code': log.error_code,
            'duration_ms': log.duration_ms,
            'logger_name': log.logger_name
        }
    
    def _status_history_to_dict(self, status: JobStatusHistory) -> Dict[str, Any]:
        """Convert status history object to dictionary"""
        return {
            'id': str(status.id),
            'job_run_id': str(status.job_run_id),
            'from_status': status.from_status,
            'to_status': status.to_status,
            'timestamp': status.timestamp.isoformat(),
            'reason': status.reason,
            'details': status.details
        }
    
    def _metric_to_dict(self, metric: JobMetrics) -> Dict[str, Any]:
        """Convert metric object to dictionary"""
        return {
            'id': str(metric.id),
            'job_run_id': str(metric.job_run_id),
            'timestamp': metric.timestamp.isoformat(),
            'metric_name': metric.metric_name,
            'metric_value': metric.metric_value,
            'metric_type': metric.metric_type,
            'labels': metric.labels
        }
    
    # New Elasticsearch-powered methods
    
    def search_logs_elasticsearch(self, filters: LogSearchFilters, skip: int = 0, 
                                 limit: int = 100, sort_by: str = "timestamp", 
                                 sort_order: str = "desc") -> LogSearchResponse:
        """Search logs using Elasticsearch with advanced filtering"""
        if not self.es_logger or not self.es_logger.es:
            # Fallback to database search
            return self._search_logs_database(filters, skip, limit, sort_by, sort_order)
        
        try:
            start_time = datetime.now()
            
            # Build Elasticsearch query
            query = self._build_elasticsearch_query(filters)
            
            # Build sort
            sort = [{sort_by: {"order": sort_order}}]
            
            # Execute search
            response = self.es_logger.es.search(
                index=f"{self.es_logger.index_prefix}-job-logs-*",
                body={
                    "query": query,
                    "sort": sort,
                    "from": skip,
                    "size": limit,
                    "_source": True
                }
            )
            
            # Convert hits to JobLogResponse
            logs = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                logs.append(JobLogResponse(
                    id=hit["_id"],
                    job_run_id=source.get("job_run_id", ""),
                    timestamp=datetime.fromisoformat(source.get("timestamp", "")),
                    level=source.get("level", "INFO"),
                    message=source.get("message", ""),
                    details=source.get("details"),
                    step=source.get("step"),
                    paper_id=source.get("paper_id"),
                    error_code=source.get("error_code"),
                    duration_ms=source.get("duration_ms"),
                    logger_name=source.get("logger_name")
                ))
            
            total = response["hits"]["total"]["value"]
            search_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return LogSearchResponse(
                logs=logs,
                total=total,
                skip=skip,
                limit=limit,
                has_more=skip + len(logs) < total,
                search_time_ms=search_time_ms
            )
            
        except Exception as e:
            logger.error(f"Elasticsearch search failed: {e}")
            # Fallback to database search
            return self._search_logs_database(filters, skip, limit, sort_by, sort_order)
    
    def _build_elasticsearch_query(self, filters: LogSearchFilters) -> Dict[str, Any]:
        """Build Elasticsearch query from filters"""
        must_clauses = []
        
        # Job filters
        if filters.job_id:
            must_clauses.append({"term": {"job_id": filters.job_id}})
        if filters.job_run_id:
            must_clauses.append({"term": {"job_run_id": filters.job_run_id}})
        
        # Level filter
        if filters.level:
            must_clauses.append({"term": {"level": filters.level.value}})
        
        # Step filter
        if filters.step:
            must_clauses.append({"term": {"step": filters.step}})
        
        # Paper ID filter
        if filters.paper_id:
            must_clauses.append({"term": {"paper_id": filters.paper_id}})
        
        # Error code filter
        if filters.error_code:
            must_clauses.append({"term": {"error_code": filters.error_code}})
        
        # Time range filter
        if filters.start_time or filters.end_time:
            time_range = {}
            if filters.start_time:
                time_range["gte"] = filters.start_time.isoformat()
            if filters.end_time:
                time_range["lte"] = filters.end_time.isoformat()
            must_clauses.append({"range": {"timestamp": time_range}})
        
        # Text search
        if filters.search:
            must_clauses.append({
                "multi_match": {
                    "query": filters.search,
                    "fields": ["message^2", "details.*", "step", "error_code"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        # Build final query
        if not must_clauses:
            return {"match_all": {}}
        elif len(must_clauses) == 1:
            return must_clauses[0]
        else:
            return {"bool": {"must": must_clauses}}
    
    def _search_logs_database(self, filters: LogSearchFilters, skip: int = 0, 
                             limit: int = 100, sort_by: str = "timestamp", 
                             sort_order: str = "desc") -> LogSearchResponse:
        """Fallback database search when Elasticsearch is not available"""
        try:
            start_time = datetime.now()
            
            # Build database query
            query = self.db_session.query(JobLog)
            
            # Apply filters
            if filters.job_run_id:
                query = query.filter(JobLog.job_run_id == filters.job_run_id)
            if filters.level:
                query = query.filter(JobLog.level == filters.level.value)
            if filters.step:
                query = query.filter(JobLog.step == filters.step)
            if filters.paper_id:
                query = query.filter(JobLog.paper_id == filters.paper_id)
            if filters.error_code:
                query = query.filter(JobLog.error_code == filters.error_code)
            if filters.start_time:
                query = query.filter(JobLog.timestamp >= filters.start_time)
            if filters.end_time:
                query = query.filter(JobLog.timestamp <= filters.end_time)
            if filters.search:
                query = query.filter(JobLog.message.ilike(f"%{filters.search}%"))
            
            # Get total count
            total = query.count()
            
            # Apply sorting
            if sort_by == "timestamp":
                if sort_order == "desc":
                    query = query.order_by(JobLog.timestamp.desc())
                else:
                    query = query.order_by(JobLog.timestamp.asc())
            # Add more sort options as needed
            
            # Apply pagination
            logs_data = query.offset(skip).limit(limit).all()
            
            # Convert to response format
            logs = [
                JobLogResponse(
                    id=str(log.id),
                    job_run_id=str(log.job_run_id),
                    timestamp=log.timestamp,
                    level=log.level,
                    message=log.message,
                    details=log.details,
                    step=log.step,
                    paper_id=log.paper_id,
                    error_code=log.error_code,
                    duration_ms=log.duration_ms,
                    logger_name=log.logger_name
                )
                for log in logs_data
            ]
            
            search_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return LogSearchResponse(
                logs=logs,
                total=total,
                skip=skip,
                limit=limit,
                has_more=skip + len(logs) < total,
                search_time_ms=search_time_ms
            )
            
        except Exception as e:
            logger.error(f"Database search failed: {e}")
            raise ServiceError(f"Failed to search logs: {str(e)}")
    
    def get_log_aggregations(self, filters: LogSearchFilters) -> Dict[str, Any]:
        """Get log aggregations from Elasticsearch"""
        if not self.es_logger or not self.es_logger.es:
            return self._get_log_aggregations_database(filters)
        
        try:
            query = self._build_elasticsearch_query(filters)
            
            response = self.es_logger.es.search(
                index=f"{self.es_logger.index_prefix}-job-logs-*",
                body={
                    "query": query,
                    "size": 0,
                    "aggs": {
                        "levels": {
                            "terms": {"field": "level", "size": 10}
                        },
                        "steps": {
                            "terms": {"field": "step", "size": 20}
                        },
                        "error_codes": {
                            "terms": {"field": "error_code", "size": 20}
                        },
                        "timeline": {
                            "date_histogram": {
                                "field": "timestamp",
                                "calendar_interval": "hour"
                            }
                        }
                    }
                }
            )
            
            return {
                "levels": {bucket["key"]: bucket["doc_count"] for bucket in response["aggregations"]["levels"]["buckets"]},
                "steps": {bucket["key"]: bucket["doc_count"] for bucket in response["aggregations"]["steps"]["buckets"]},
                "error_codes": {bucket["key"]: bucket["doc_count"] for bucket in response["aggregations"]["error_codes"]["buckets"]},
                "timeline": [
                    {
                        "timestamp": bucket["key_as_string"],
                        "count": bucket["doc_count"]
                    }
                    for bucket in response["aggregations"]["timeline"]["buckets"]
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get log aggregations from Elasticsearch: {e}")
            return self._get_log_aggregations_database(filters)
    
    def _get_log_aggregations_database(self, filters: LogSearchFilters) -> Dict[str, Any]:
        """Fallback database aggregations"""
        try:
            # This is a simplified version - you might want to implement more sophisticated aggregations
            from sqlalchemy import func
            
            query = self.db_session.query(JobLog)
            
            # Apply same filters as search
            if filters.job_run_id:
                query = query.filter(JobLog.job_run_id == filters.job_run_id)
            # ... apply other filters
            
            # Get level counts
            level_counts = dict(
                self.db_session.query(JobLog.level, func.count(JobLog.id))
                .group_by(JobLog.level)
                .all()
            )
            
            return {
                "levels": level_counts,
                "steps": {},
                "error_codes": {},
                "timeline": []
            }
            
        except Exception as e:
            logger.error(f"Failed to get database aggregations: {e}")
            return {"levels": {}, "steps": {}, "error_codes": {}, "timeline": []} 