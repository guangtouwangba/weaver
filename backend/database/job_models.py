#!/usr/bin/env python3
"""
Database models for job scheduling system
Defines the structure for jobs, job executions, and related data
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import json

class JobStatus(Enum):
    """Job status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    DELETED = "deleted"

class JobType(Enum):
    """Job type enumeration"""
    PAPER_FETCH = "paper_fetch"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"

class ExecutionStatus(Enum):
    """Job execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class Job:
    """Job model representing a scheduled task"""
    
    def __init__(self, 
                 name: str,
                 job_type: JobType,
                 schedule_expression: str,
                 config: Dict[str, Any],
                 job_id: str = None,
                 status: JobStatus = JobStatus.ACTIVE,
                 description: str = "",
                 timeout_seconds: int = 3600,
                 retry_count: int = 3,
                 retry_delay_seconds: int = 300,
                 created_at: datetime = None,
                 updated_at: datetime = None,
                 last_execution: datetime = None,
                 next_execution: datetime = None):
        
        self.job_id = job_id or str(uuid.uuid4())
        self.name = name
        self.job_type = job_type
        self.schedule_expression = schedule_expression
        self.config = config
        self.status = status
        self.description = description
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.retry_delay_seconds = retry_delay_seconds
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.last_execution = last_execution
        self.next_execution = next_execution
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for database storage"""
        return {
            'job_id': self.job_id,
            'name': self.name,
            'job_type': self.job_type.value if isinstance(self.job_type, JobType) else self.job_type,
            'schedule_expression': self.schedule_expression,
            'config': json.dumps(self.config) if isinstance(self.config, dict) else self.config,
            'status': self.status.value if isinstance(self.status, JobStatus) else self.status,
            'description': self.description,
            'timeout_seconds': self.timeout_seconds,
            'retry_count': self.retry_count,
            'retry_delay_seconds': self.retry_delay_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary"""
        return cls(
            job_id=data.get('job_id'),
            name=data['name'],
            job_type=JobType(data['job_type']) if isinstance(data.get('job_type'), str) else data['job_type'],
            schedule_expression=data['schedule_expression'],
            config=json.loads(data['config']) if isinstance(data.get('config'), str) else data.get('config', {}),
            status=JobStatus(data['status']) if isinstance(data.get('status'), str) else data.get('status', JobStatus.ACTIVE),
            description=data.get('description', ''),
            timeout_seconds=data.get('timeout_seconds', 3600),
            retry_count=data.get('retry_count', 3),
            retry_delay_seconds=data.get('retry_delay_seconds', 300),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            last_execution=datetime.fromisoformat(data['last_execution']) if data.get('last_execution') else None,
            next_execution=datetime.fromisoformat(data['next_execution']) if data.get('next_execution') else None
        )

class JobExecution:
    """Job execution model representing a single run of a job"""
    
    def __init__(self,
                 job_id: str,
                 execution_id: str = None,
                 status: ExecutionStatus = ExecutionStatus.PENDING,
                 started_at: datetime = None,
                 finished_at: datetime = None,
                 duration_seconds: float = None,
                 result: Dict[str, Any] = None,
                 error_message: str = None,
                 retry_attempt: int = 0,
                 logs: str = None,
                 created_at: datetime = None):
        
        self.execution_id = execution_id or str(uuid.uuid4())
        self.job_id = job_id
        self.status = status
        self.started_at = started_at
        self.finished_at = finished_at
        self.duration_seconds = duration_seconds
        self.result = result or {}
        self.error_message = error_message
        self.retry_attempt = retry_attempt
        self.logs = logs or ""
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job execution to dictionary for database storage"""
        return {
            'execution_id': self.execution_id,
            'job_id': self.job_id,
            'status': self.status.value if isinstance(self.status, ExecutionStatus) else self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'duration_seconds': self.duration_seconds,
            'result': json.dumps(self.result) if isinstance(self.result, dict) else self.result,
            'error_message': self.error_message,
            'retry_attempt': self.retry_attempt,
            'logs': self.logs,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobExecution':
        """Create job execution from dictionary"""
        return cls(
            execution_id=data.get('execution_id'),
            job_id=data['job_id'],
            status=ExecutionStatus(data['status']) if isinstance(data.get('status'), str) else data.get('status', ExecutionStatus.PENDING),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            finished_at=datetime.fromisoformat(data['finished_at']) if data.get('finished_at') else None,
            duration_seconds=data.get('duration_seconds'),
            result=json.loads(data['result']) if isinstance(data.get('result'), str) else data.get('result', {}),
            error_message=data.get('error_message'),
            retry_attempt=data.get('retry_attempt', 0),
            logs=data.get('logs', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )
    
    def mark_started(self):
        """Mark execution as started"""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def mark_completed(self, result: Dict[str, Any] = None, logs: str = None):
        """Mark execution as completed successfully"""
        self.status = ExecutionStatus.SUCCESS
        self.finished_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
        if result:
            self.result = result
        if logs:
            self.logs = logs
    
    def mark_failed(self, error_message: str, logs: str = None):
        """Mark execution as failed"""
        self.status = ExecutionStatus.FAILED
        self.finished_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
        self.error_message = error_message
        if logs:
            self.logs = logs
    
    def mark_timeout(self, logs: str = None):
        """Mark execution as timed out"""
        self.status = ExecutionStatus.TIMEOUT
        self.finished_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
        self.error_message = "Execution timed out"
        if logs:
            self.logs = logs

# Utility functions for schedule expressions

def parse_cron_expression(expression: str) -> Dict[str, Any]:
    """
    Parse cron expression into components
    Format: "minute hour day month weekday"
    Examples:
    - "0 */2 * * *" - Every 2 hours
    - "0 9 * * 1-5" - 9 AM on weekdays
    - "*/15 * * * *" - Every 15 minutes
    """
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {expression}. Must have 5 parts.")
    
    return {
        'minute': parts[0],
        'hour': parts[1],
        'day': parts[2],
        'month': parts[3],
        'weekday': parts[4]
    }

def validate_schedule_expression(expression: str) -> bool:
    """Validate schedule expression format"""
    try:
        parse_cron_expression(expression)
        return True
    except ValueError:
        return False