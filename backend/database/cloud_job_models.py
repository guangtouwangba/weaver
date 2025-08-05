#!/usr/bin/env python3
"""
Simplified Cloud Job Models
Lightweight models for cloud-native job execution
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import json

class CloudJobStatus(Enum):
    """Simplified job status for cloud execution"""
    WAITING = "waiting"      # Ready to be executed
    LOCKED = "locked"        # Currently being executed
    SUCCESS = "success"      # Completed successfully
    FAILED = "failed"        # Failed execution
    DISABLED = "disabled"    # Temporarily disabled

class CloudJobType(Enum):
    """Job type enumeration"""
    PAPER_FETCH = "paper_fetch"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"

class CloudJob:
    """Simplified job model for cloud execution"""
    
    def __init__(self, 
                 name: str,
                 job_type: CloudJobType,
                 config: Dict[str, Any],
                 job_id: str = None,
                 status: CloudJobStatus = CloudJobStatus.WAITING,
                 description: str = "",
                 max_retries: int = 3,
                 current_retries: int = 0,
                 created_at: datetime = None,
                 last_execution: datetime = None,
                 locked_at: datetime = None,
                 locked_by: str = None,
                 lock_expires_at: datetime = None):
        
        self.job_id = job_id or str(uuid.uuid4())
        self.name = name
        self.job_type = job_type if isinstance(job_type, CloudJobType) else CloudJobType(job_type)
        self.config = config or {}
        self.status = status if isinstance(status, CloudJobStatus) else CloudJobStatus(status)
        self.description = description
        self.max_retries = max_retries
        self.current_retries = current_retries
        self.created_at = created_at or datetime.utcnow()
        self.last_execution = last_execution
        
        # Lock mechanism fields
        self.locked_at = locked_at
        self.locked_by = locked_by  # Instance ID that locked the job
        self.lock_expires_at = lock_expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for database storage"""
        return {
            'job_id': self.job_id,
            'name': self.name,
            'job_type': self.job_type.value,
            'config': json.dumps(self.config),
            'status': self.status.value,
            'description': self.description,
            'max_retries': self.max_retries,
            'current_retries': self.current_retries,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'locked_at': self.locked_at.isoformat() if self.locked_at else None,
            'locked_by': self.locked_by,
            'lock_expires_at': self.lock_expires_at.isoformat() if self.lock_expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CloudJob':
        """Create job from dictionary data"""
        return cls(
            job_id=data.get('job_id'),
            name=data['name'],
            job_type=CloudJobType(data['job_type']),
            config=json.loads(data.get('config', '{}')),
            status=CloudJobStatus(data.get('status', 'waiting')),
            description=data.get('description', ''),
            max_retries=data.get('max_retries', 3),
            current_retries=data.get('current_retries', 0),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            last_execution=datetime.fromisoformat(data['last_execution']) if data.get('last_execution') else None,
            locked_at=datetime.fromisoformat(data['locked_at']) if data.get('locked_at') else None,
            locked_by=data.get('locked_by'),
            lock_expires_at=datetime.fromisoformat(data['lock_expires_at']) if data.get('lock_expires_at') else None
        )
    
    def is_locked(self) -> bool:
        """Check if job is currently locked"""
        if self.status != CloudJobStatus.LOCKED:
            return False
        
        # Check if lock has expired
        if self.lock_expires_at and datetime.utcnow() > self.lock_expires_at:
            return False
        
        return True
    
    def can_execute(self) -> bool:
        """Check if job can be executed"""
        return (self.status == CloudJobStatus.WAITING or 
                (self.status == CloudJobStatus.FAILED and self.current_retries < self.max_retries))
    
    def should_retry(self) -> bool:
        """Check if job should be retried after failure"""
        return self.status == CloudJobStatus.FAILED and self.current_retries < self.max_retries

class CloudJobExecution:
    """Simplified job execution record"""
    
    def __init__(self,
                 job_id: str,
                 execution_id: str = None,
                 status: str = "running",
                 started_at: datetime = None,
                 finished_at: datetime = None,
                 duration_seconds: float = None,
                 result: Dict[str, Any] = None,
                 error_message: str = None,
                 instance_id: str = None):
        
        self.execution_id = execution_id or str(uuid.uuid4())
        self.job_id = job_id
        self.status = status
        self.started_at = started_at or datetime.utcnow()
        self.finished_at = finished_at
        self.duration_seconds = duration_seconds
        self.result = result or {}
        self.error_message = error_message
        self.instance_id = instance_id
    
    def mark_completed(self, result: Dict[str, Any] = None):
        """Mark execution as completed"""
        self.finished_at = datetime.utcnow()
        self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
        self.status = "success"
        if result:
            self.result = result
    
    def mark_failed(self, error_message: str):
        """Mark execution as failed"""
        self.finished_at = datetime.utcnow()
        self.duration_seconds = (self.finished_at - self.started_at).total_seconds()
        self.status = "failed"
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution to dictionary for database storage"""
        return {
            'execution_id': self.execution_id,
            'job_id': self.job_id,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'duration_seconds': self.duration_seconds,
            'result': json.dumps(self.result),
            'error_message': self.error_message,
            'instance_id': self.instance_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CloudJobExecution':
        """Create execution from dictionary data"""
        return cls(
            execution_id=data.get('execution_id'),
            job_id=data['job_id'],
            status=data.get('status', 'running'),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            finished_at=datetime.fromisoformat(data['finished_at']) if data.get('finished_at') else None,
            duration_seconds=data.get('duration_seconds'),
            result=json.loads(data.get('result', '{}')),
            error_message=data.get('error_message'),
            instance_id=data.get('instance_id')
        )