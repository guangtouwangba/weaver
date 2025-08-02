"""
Elasticsearch Logger - Store job logs in Elasticsearch for advanced search and analytics
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import ConnectionError, RequestError
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    logger.warning("Elasticsearch not available. Install with: pip install elasticsearch")
    Elasticsearch = None
    ConnectionError = Exception
    RequestError = Exception
    ELASTICSEARCH_AVAILABLE = False

class ElasticsearchLogger:
    """Elasticsearch logger for job logs"""
    
    def __init__(self, 
                 hosts: List[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 index_prefix: str = "job-logs"):
        """
        Initialize Elasticsearch logger
        
        Args:
            hosts: List of Elasticsearch hosts (e.g., ['http://localhost:9200'])
            username: Elasticsearch username
            password: Elasticsearch password
            index_prefix: Prefix for index names
        """
        if not ELASTICSEARCH_AVAILABLE:
            logger.warning("Elasticsearch not available - ElasticsearchLogger will use dummy operations")
            self.es = None
            return
            
        self.hosts = hosts or ['http://localhost:9200']
        self.username = username
        self.password = password
        self.index_prefix = index_prefix
        
        # Initialize Elasticsearch client
        try:
            self.es = self._create_client()
            # Create index templates
            if self.es:
                self._create_index_templates()
        except Exception as e:
            logger.warning(f"Failed to initialize Elasticsearch client: {e}")
            self.es = None
    
    def _create_client(self) -> Optional[Elasticsearch]:
        """Create Elasticsearch client"""
        try:
            if self.username and self.password:
                es = Elasticsearch(
                    hosts=self.hosts,
                    basic_auth=(self.username, self.password),
                    timeout=30,
                    max_retries=3,
                    retry_on_timeout=True
                )
            else:
                es = Elasticsearch(
                    hosts=self.hosts,
                    timeout=30,
                    max_retries=3,
                    retry_on_timeout=True
                )
            
            # Test connection
            if es.ping():
                logger.info("Successfully connected to Elasticsearch")
                return es
            else:
                logger.warning("Could not ping Elasticsearch - returning None")
                return None
            
        except Exception as e:
            logger.warning(f"Failed to create Elasticsearch client: {e}")
            return None
    
    def _create_index_templates(self):
        """Create index templates for job logs"""
        if not self.es:
            logger.warning("Elasticsearch client not available, skipping index template creation")
            return
            
        try:
            # Template for job logs
            job_logs_template = {
                "index_patterns": [f"{self.index_prefix}-job-logs-*"],
                "template": {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "refresh_interval": "1s"
                    },
                    "mappings": {
                        "properties": {
                            "job_run_id": {"type": "keyword"},
                            "job_id": {"type": "keyword"},
                            "timestamp": {"type": "date"},
                            "level": {"type": "keyword"},
                            "message": {"type": "text", "analyzer": "standard"},
                            "details": {"type": "object", "enabled": True},
                            "step": {"type": "keyword"},
                            "paper_id": {"type": "keyword"},
                            "error_code": {"type": "keyword"},
                            "duration_ms": {"type": "long"},
                            "logger_name": {"type": "keyword"},
                            "job_name": {"type": "keyword"},
                            "status": {"type": "keyword"}
                        }
                    }
                }
            }
            
            # Template for status history
            status_history_template = {
                "index_patterns": [f"{self.index_prefix}-status-history-*"],
                "template": {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "refresh_interval": "1s"
                    },
                    "mappings": {
                        "properties": {
                            "job_run_id": {"type": "keyword"},
                            "job_id": {"type": "keyword"},
                            "from_status": {"type": "keyword"},
                            "to_status": {"type": "keyword"},
                            "timestamp": {"type": "date"},
                            "reason": {"type": "text"},
                            "details": {"type": "object", "enabled": True}
                        }
                    }
                }
            }
            
            # Template for metrics
            metrics_template = {
                "index_patterns": [f"{self.index_prefix}-metrics-*"],
                "template": {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "refresh_interval": "1s"
                    },
                    "mappings": {
                        "properties": {
                            "job_run_id": {"type": "keyword"},
                            "job_id": {"type": "keyword"},
                            "timestamp": {"type": "date"},
                            "metric_name": {"type": "keyword"},
                            "metric_value": {"type": "long"},
                            "metric_type": {"type": "keyword"},
                            "labels": {"type": "object", "enabled": True}
                        }
                    }
                }
            }
            
            # Create templates
            self.es.indices.put_index_template(
                name=f"{self.index_prefix}-job-logs-template",
                body=job_logs_template
            )
            
            self.es.indices.put_index_template(
                name=f"{self.index_prefix}-status-history-template",
                body=status_history_template
            )
            
            self.es.indices.put_index_template(
                name=f"{self.index_prefix}-metrics-template",
                body=metrics_template
            )
            
            logger.info("Successfully created Elasticsearch index templates")
            
        except Exception as e:
            logger.error(f"Failed to create index templates: {e}")
    
    def _get_index_name(self, doc_type: str, job_run_id: str = None) -> str:
        """Generate index name with date suffix"""
        from datetime import datetime
        date_suffix = datetime.now().strftime("%Y.%m.%d")
        
        if job_run_id:
            # Create job-specific index for better isolation
            return f"{self.index_prefix}-{doc_type}-{job_run_id}-{date_suffix}"
        else:
            return f"{self.index_prefix}-{doc_type}-{date_suffix}"
    
    def log_job_event(self, 
                     job_run_id: str,
                     job_id: str,
                     job_name: str,
                     level: str,
                     message: str,
                     **kwargs) -> bool:
        """
        Log a job event to Elasticsearch
        
        Args:
            job_run_id: Job run ID
            job_id: Job ID
            job_name: Job name
            level: Log level
            message: Log message
            **kwargs: Additional fields (step, paper_id, error_code, duration_ms, etc.)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not ELASTICSEARCH_AVAILABLE or not self.es:
            logger.debug(f"Elasticsearch not available - skipping log event: {message}")
            return True
            
        try:
            doc = {
                "job_run_id": job_run_id,
                "job_id": job_id,
                "job_name": job_name,
                "timestamp": datetime.now().isoformat(),
                "level": level.upper(),
                "message": message,
                **kwargs
            }
            
            # Remove None values
            doc = {k: v for k, v in doc.items() if v is not None}
            
            index_name = self._get_index_name("job-logs", job_run_id)
            
            response = self.es.index(
                index=index_name,
                document=doc,
                refresh=True
            )
            
            logger.debug(f"Logged to Elasticsearch: {response['_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log to Elasticsearch: {e}")
            return False
    
    def log_status_change(self,
                         job_run_id: str,
                         job_id: str,
                         from_status: Optional[str],
                         to_status: str,
                         reason: Optional[str] = None,
                         details: Optional[Dict] = None) -> bool:
        """
        Log a status change to Elasticsearch
        
        Args:
            job_run_id: Job run ID
            job_id: Job ID
            from_status: Previous status
            to_status: New status
            reason: Reason for status change
            details: Additional details
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not ELASTICSEARCH_AVAILABLE or not self.es:
            logger.debug(f"Elasticsearch not available - skipping status change log")
            return True
            
        try:
            doc = {
                "job_run_id": job_run_id,
                "job_id": job_id,
                "from_status": from_status,
                "to_status": to_status,
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "details": details
            }
            
            # Remove None values
            doc = {k: v for k, v in doc.items() if v is not None}
            
            index_name = self._get_index_name("status-history", job_run_id)
            
            response = self.es.index(
                index=index_name,
                document=doc,
                refresh=True
            )
            
            logger.debug(f"Logged status change to Elasticsearch: {response['_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log status change to Elasticsearch: {e}")
            return False
    
    def log_metric(self,
                  job_run_id: str,
                  job_id: str,
                  metric_name: str,
                  metric_value: int,
                  metric_type: str = "counter",
                  labels: Optional[Dict] = None) -> bool:
        """
        Log a metric to Elasticsearch
        
        Args:
            job_run_id: Job run ID
            job_id: Job ID
            metric_name: Name of the metric
            metric_value: Value of the metric
            metric_type: Type of metric (counter, gauge, histogram)
            labels: Additional labels
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not ELASTICSEARCH_AVAILABLE or not self.es:
            logger.debug(f"Elasticsearch not available - skipping metric log")
            return True
            
        try:
            doc = {
                "job_run_id": job_run_id,
                "job_id": job_id,
                "timestamp": datetime.now().isoformat(),
                "metric_name": metric_name,
                "metric_value": metric_value,
                "metric_type": metric_type,
                "labels": labels
            }
            
            # Remove None values
            doc = {k: v for k, v in doc.items() if v is not None}
            
            index_name = self._get_index_name("metrics", job_run_id)
            
            response = self.es.index(
                index=index_name,
                document=doc,
                refresh=True
            )
            
            logger.debug(f"Logged metric to Elasticsearch: {response['_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log metric to Elasticsearch: {e}")
            return False
    
    def search_logs(self,
                   job_run_id: Optional[str] = None,
                   job_id: Optional[str] = None,
                   level: Optional[str] = None,
                   step: Optional[str] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   size: int = 100) -> List[Dict]:
        """
        Search logs in Elasticsearch
        
        Args:
            job_run_id: Filter by job run ID
            job_id: Filter by job ID
            level: Filter by log level
            step: Filter by step
            start_time: Start time for range query
            end_time: End time for range query
            size: Number of results to return
        
        Returns:
            List of log documents
        """
        if not ELASTICSEARCH_AVAILABLE or not self.es:
            logger.debug(f"Elasticsearch not available - returning empty list")
            return []
            
        try:
            query = {"bool": {"must": []}}
            
            if job_run_id:
                query["bool"]["must"].append({"term": {"job_run_id": job_run_id}})
            
            if job_id:
                query["bool"]["must"].append({"term": {"job_id": job_id}})
            
            if level:
                query["bool"]["must"].append({"term": {"level": level.upper()}})
            
            if step:
                query["bool"]["must"].append({"term": {"step": step}})
            
            if start_time or end_time:
                time_range = {}
                if start_time:
                    time_range["gte"] = start_time.isoformat()
                if end_time:
                    time_range["lte"] = end_time.isoformat()
                
                query["bool"]["must"].append({"range": {"timestamp": time_range}})
            
            # If no filters, match all
            if not query["bool"]["must"]:
                query = {"match_all": {}}
            
            # Determine index pattern
            if job_run_id:
                index_pattern = f"{self.index_prefix}-job-logs-{job_run_id}-*"
            else:
                index_pattern = f"{self.index_prefix}-job-logs-*"
            
            response = self.es.search(
                index=index_pattern,
                body={
                    "query": query,
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": size
                }
            )
            
            return [hit["_source"] for hit in response["hits"]["hits"]]
            
        except Exception as e:
            logger.error(f"Failed to search logs in Elasticsearch: {e}")
            return []
    
    def get_log_statistics(self,
                          job_run_id: Optional[str] = None,
                          job_id: Optional[str] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> Dict:
        """
        Get log statistics from Elasticsearch
        
        Args:
            job_run_id: Filter by job run ID
            job_id: Filter by job ID
            start_time: Start time for range query
            end_time: End time for range query
        
        Returns:
            Dictionary with statistics
        """
        if not ELASTICSEARCH_AVAILABLE or not self.es:
            logger.debug(f"Elasticsearch not available - returning empty statistics")
            return {}
            
        try:
            query = {"bool": {"must": []}}
            
            if job_run_id:
                query["bool"]["must"].append({"term": {"job_run_id": job_run_id}})
            
            if job_id:
                query["bool"]["must"].append({"term": {"job_id": job_id}})
            
            if start_time or end_time:
                time_range = {}
                if start_time:
                    time_range["gte"] = start_time.isoformat()
                if end_time:
                    time_range["lte"] = end_time.isoformat()
                
                query["bool"]["must"].append({"range": {"timestamp": time_range}})
            
            # If no filters, match all
            if not query["bool"]["must"]:
                query = {"match_all": {}}
            
            # Determine index pattern
            if job_run_id:
                index_pattern = f"{self.index_prefix}-job-logs-{job_run_id}-*"
            else:
                index_pattern = f"{self.index_prefix}-job-logs-*"
            
            response = self.es.search(
                index=index_pattern,
                body={
                    "query": query,
                    "aggs": {
                        "level_counts": {
                            "terms": {"field": "level"}
                        },
                        "step_counts": {
                            "terms": {"field": "step"}
                        },
                        "total_logs": {
                            "value_count": {"field": "job_run_id"}
                        }
                    },
                    "size": 0
                }
            )
            
            aggs = response["aggregations"]
            
            return {
                "total_logs": aggs["total_logs"]["value"],
                "level_counts": {bucket["key"]: bucket["doc_count"] for bucket in aggs["level_counts"]["buckets"]},
                "step_counts": {bucket["key"]: bucket["doc_count"] for bucket in aggs["step_counts"]["buckets"]}
            }
            
        except Exception as e:
            logger.error(f"Failed to get log statistics from Elasticsearch: {e}")
            return {}
    
    def close(self):
        """Close Elasticsearch connection"""
        if hasattr(self, 'es'):
            self.es.close()

class ElasticsearchLoggerFactory:
    """Factory for creating Elasticsearch loggers"""
    
    @staticmethod
    def create_logger(hosts: List[str] = None,
                     username: Optional[str] = None,
                     password: Optional[str] = None,
                     index_prefix: str = "job-logs") -> ElasticsearchLogger:
        """Create a new Elasticsearch logger instance"""
        return ElasticsearchLogger(hosts, username, password, index_prefix) 