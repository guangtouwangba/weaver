"""
Error handling and recovery mechanisms for task processing.

Provides comprehensive error handling, retry logic,
and recovery strategies for different types of failures.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any, Type
from datetime import datetime, timedelta
from enum import Enum
import traceback
import inspect

from .models import ProcessingTask, TaskError, TaskStatus

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categories of errors for different handling strategies."""
    TRANSIENT = "transient"          # Temporary failures, retry immediately
    RATE_LIMITED = "rate_limited"    # Rate limiting, retry with backoff
    RESOURCE = "resource"            # Resource exhaustion, wait and retry
    CONFIGURATION = "configuration"  # Config errors, manual intervention needed
    DATA = "data"                   # Data/content issues, may need preprocessing
    SYSTEM = "system"               # System failures, escalate
    PERMANENT = "permanent"          # Permanent failures, don't retry


class RetryStrategy(str, Enum):
    """Retry strategies for different error types."""
    IMMEDIATE = "immediate"          # Retry immediately
    LINEAR_BACKOFF = "linear"       # Linear backoff (delay * attempt)
    EXPONENTIAL_BACKOFF = "exponential"  # Exponential backoff (delay * 2^attempt)
    FIXED_DELAY = "fixed"           # Fixed delay between retries
    CUSTOM = "custom"               # Custom retry logic


class ErrorPattern:
    """Defines how to handle specific error patterns."""
    
    def __init__(
        self,
        name: str,
        category: ErrorCategory,
        retry_strategy: RetryStrategy,
        max_retries: int = 3,
        base_delay: int = 60,
        max_delay: int = 3600,
        error_codes: Optional[List[str]] = None,
        exception_types: Optional[List[Type[Exception]]] = None,
        message_patterns: Optional[List[str]] = None,
        custom_handler: Optional[Callable] = None
    ):
        self.name = name
        self.category = category
        self.retry_strategy = retry_strategy
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.error_codes = error_codes or []
        self.exception_types = exception_types or []
        self.message_patterns = message_patterns or []
        self.custom_handler = custom_handler

    def matches(self, error: TaskError, exception: Optional[Exception] = None) -> bool:
        """Check if this pattern matches the given error."""
        # Check error codes
        if self.error_codes and error.error_code in self.error_codes:
            return True
        
        # Check exception types
        if exception and self.exception_types:
            for exc_type in self.exception_types:
                if isinstance(exception, exc_type):
                    return True
        
        # Check message patterns
        if self.message_patterns:
            error_message = error.error_message.lower()
            for pattern in self.message_patterns:
                if pattern.lower() in error_message:
                    return True
        
        return False

    def calculate_delay(self, attempt: int) -> int:
        """Calculate retry delay based on strategy and attempt number."""
        if self.retry_strategy == RetryStrategy.IMMEDIATE:
            return 0
        elif self.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.base_delay * attempt
        elif self.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay * (2 ** (attempt - 1))
        elif self.retry_strategy == RetryStrategy.FIXED_DELAY:
            delay = self.base_delay
        else:  # CUSTOM
            delay = self.base_delay
        
        return min(delay, self.max_delay)


class TaskErrorHandler:
    """
    Comprehensive error handler for task processing.
    
    Features:
    - Pattern-based error classification
    - Intelligent retry strategies
    - Error recovery mechanisms
    - Monitoring and alerting
    - Custom error handlers
    """
    
    def __init__(self):
        self.error_patterns: List[ErrorPattern] = []
        self.error_stats: Dict[str, Dict[str, Any]] = {}
        self.recovery_handlers: Dict[ErrorCategory, List[Callable]] = {}
        self.alert_thresholds: Dict[str, int] = {
            "error_rate": 10,  # Alert if >10 errors per minute
            "failure_rate": 50,  # Alert if >50% failure rate
            "queue_size": 100   # Alert if queue size >100
        }
        
        # Initialize default error patterns
        self._setup_default_patterns()
        
        logger.info("TaskErrorHandler initialized")

    def _setup_default_patterns(self):
        """Set up default error handling patterns."""
        
        # Network/API related errors
        self.add_pattern(ErrorPattern(
            name="network_timeout",
            category=ErrorCategory.TRANSIENT,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=3,
            base_delay=30,
            error_codes=["NETWORK_TIMEOUT", "CONNECTION_ERROR"],
            exception_types=[asyncio.TimeoutError, ConnectionError],
            message_patterns=["timeout", "connection", "network"]
        ))
        
        # Rate limiting
        self.add_pattern(ErrorPattern(
            name="rate_limited",
            category=ErrorCategory.RATE_LIMITED,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=5,
            base_delay=120,
            max_delay=3600,
            error_codes=["RATE_LIMITED", "TOO_MANY_REQUESTS"],
            message_patterns=["rate limit", "too many requests", "quota exceeded"]
        ))
        
        # Resource exhaustion
        self.add_pattern(ErrorPattern(
            name="resource_exhaustion",
            category=ErrorCategory.RESOURCE,
            retry_strategy=RetryStrategy.LINEAR_BACKOFF,
            max_retries=3,
            base_delay=300,
            error_codes=["OUT_OF_MEMORY", "DISK_FULL", "CPU_OVERLOAD"],
            message_patterns=["out of memory", "disk full", "resource", "overload"]
        ))
        
        # File access errors
        self.add_pattern(ErrorPattern(
            name="file_access",
            category=ErrorCategory.DATA,
            retry_strategy=RetryStrategy.FIXED_DELAY,
            max_retries=2,
            base_delay=60,
            error_codes=["FILE_NOT_FOUND", "PERMISSION_DENIED", "FILE_LOCKED"],
            exception_types=[FileNotFoundError, PermissionError],
            message_patterns=["file not found", "permission denied", "access denied"]
        ))
        
        # Configuration errors
        self.add_pattern(ErrorPattern(
            name="configuration",
            category=ErrorCategory.CONFIGURATION,
            retry_strategy=RetryStrategy.FIXED_DELAY,
            max_retries=1,
            base_delay=60,
            error_codes=["CONFIG_ERROR", "INVALID_CONFIG", "MISSING_CONFIG"],
            message_patterns=["configuration", "config", "invalid", "missing"]
        ))
        
        # Parsing/content errors
        self.add_pattern(ErrorPattern(
            name="content_error",
            category=ErrorCategory.DATA,
            retry_strategy=RetryStrategy.IMMEDIATE,
            max_retries=1,
            base_delay=0,
            error_codes=["PARSE_ERROR", "INVALID_FORMAT", "CORRUPT_FILE"],
            message_patterns=["parse", "format", "corrupt", "invalid content"]
        ))
        
        # System failures
        self.add_pattern(ErrorPattern(
            name="system_failure",
            category=ErrorCategory.SYSTEM,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=2,
            base_delay=300,
            error_codes=["SYSTEM_ERROR", "SERVICE_UNAVAILABLE"],
            message_patterns=["system", "service unavailable", "internal error"]
        ))

    def add_pattern(self, pattern: ErrorPattern):
        """Add an error handling pattern."""
        self.error_patterns.append(pattern)
        logger.info(f"Added error pattern: {pattern.name}")

    def remove_pattern(self, pattern_name: str):
        """Remove an error handling pattern."""
        self.error_patterns = [p for p in self.error_patterns if p.name != pattern_name]
        logger.info(f"Removed error pattern: {pattern_name}")

    async def handle_task_error(
        self,
        task: ProcessingTask,
        error: TaskError,
        exception: Optional[Exception] = None
    ) -> bool:
        """
        Handle a task error and determine retry strategy.
        
        Returns:
            bool: True if task should be retried, False otherwise
        """
        # Find matching error pattern
        matching_pattern = self._find_matching_pattern(error, exception)
        
        if not matching_pattern:
            # No pattern matched, use default handling
            matching_pattern = self._get_default_pattern(error, exception)
        
        # Update error statistics
        self._update_error_stats(task, error, matching_pattern)
        
        # Determine if should retry
        should_retry = self._should_retry(task, error, matching_pattern)
        
        if should_retry:
            # Calculate retry delay
            delay = matching_pattern.calculate_delay(error.retry_count + 1)
            task.retry_delay_seconds = delay
            
            # Update retry settings
            task.max_retries = min(task.max_retries, matching_pattern.max_retries)
            
            logger.info(
                f"Task {task.task_id} will be retried in {delay}s "
                f"(pattern: {matching_pattern.name}, attempt: {error.retry_count + 1})"
            )
        else:
            logger.warning(
                f"Task {task.task_id} will not be retried "
                f"(pattern: {matching_pattern.name}, reason: max retries or permanent failure)"
            )
        
        # Execute custom handler if available
        if matching_pattern.custom_handler:
            try:
                await self._execute_custom_handler(
                    matching_pattern.custom_handler, task, error, exception
                )
            except Exception as e:
                logger.error(f"Custom error handler failed: {e}")
        
        # Execute recovery handlers for the error category
        await self._execute_recovery_handlers(matching_pattern.category, task, error)
        
        # Check for alert conditions
        await self._check_alert_conditions(matching_pattern, task, error)
        
        return should_retry

    def _find_matching_pattern(self, error: TaskError, exception: Optional[Exception] = None) -> Optional[ErrorPattern]:
        """Find the first matching error pattern."""
        for pattern in self.error_patterns:
            if pattern.matches(error, exception):
                return pattern
        return None

    def _get_default_pattern(self, error: TaskError, exception: Optional[Exception] = None) -> ErrorPattern:
        """Get default error pattern for unmatched errors."""
        # Analyze error to determine category
        if exception:
            if isinstance(exception, (asyncio.TimeoutError, ConnectionError)):
                category = ErrorCategory.TRANSIENT
            elif isinstance(exception, (FileNotFoundError, PermissionError)):
                category = ErrorCategory.DATA
            elif isinstance(exception, (MemoryError, OSError)):
                category = ErrorCategory.RESOURCE
            else:
                category = ErrorCategory.SYSTEM
        else:
            # Analyze error message
            message = error.error_message.lower()
            if any(word in message for word in ["timeout", "connection", "network"]):
                category = ErrorCategory.TRANSIENT
            elif any(word in message for word in ["rate", "quota", "limit"]):
                category = ErrorCategory.RATE_LIMITED
            elif any(word in message for word in ["memory", "disk", "resource"]):
                category = ErrorCategory.RESOURCE
            elif any(word in message for word in ["config", "setting", "parameter"]):
                category = ErrorCategory.CONFIGURATION
            else:
                category = ErrorCategory.SYSTEM
        
        # Return appropriate default pattern
        return ErrorPattern(
            name="default",
            category=category,
            retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=3,
            base_delay=60
        )

    def _should_retry(self, task: ProcessingTask, error: TaskError, pattern: ErrorPattern) -> bool:
        """Determine if a task should be retried."""
        # Check if error is retryable
        if not error.is_retryable:
            return False
        
        # Check if we've exceeded max retries
        if error.retry_count >= pattern.max_retries:
            return False
        
        # Check category-specific conditions
        if pattern.category == ErrorCategory.PERMANENT:
            return False
        
        if pattern.category == ErrorCategory.CONFIGURATION:
            # Configuration errors usually need manual intervention
            return error.retry_count == 0  # Only retry once
        
        return True

    def _update_error_stats(self, task: ProcessingTask, error: TaskError, pattern: ErrorPattern):
        """Update error statistics for monitoring."""
        now = datetime.now()
        minute_key = now.strftime("%Y-%m-%d %H:%M")
        
        # Initialize stats if needed
        if minute_key not in self.error_stats:
            self.error_stats[minute_key] = {
                "total_errors": 0,
                "by_pattern": {},
                "by_category": {},
                "by_task_type": {}
            }
        
        stats = self.error_stats[minute_key]
        stats["total_errors"] += 1
        
        # Update by pattern
        pattern_name = pattern.name
        if pattern_name not in stats["by_pattern"]:
            stats["by_pattern"][pattern_name] = 0
        stats["by_pattern"][pattern_name] += 1
        
        # Update by category
        category = pattern.category.value
        if category not in stats["by_category"]:
            stats["by_category"][category] = 0
        stats["by_category"][category] += 1
        
        # Update by task type
        task_type = task.task_type.value
        if task_type not in stats["by_task_type"]:
            stats["by_task_type"][task_type] = 0
        stats["by_task_type"][task_type] += 1
        
        # Clean old stats (keep last 24 hours)
        cutoff_time = now - timedelta(hours=24)
        cutoff_key = cutoff_time.strftime("%Y-%m-%d %H:%M")
        
        keys_to_remove = [k for k in self.error_stats.keys() if k < cutoff_key]
        for key in keys_to_remove:
            del self.error_stats[key]

    async def _execute_custom_handler(
        self,
        handler: Callable,
        task: ProcessingTask,
        error: TaskError,
        exception: Optional[Exception]
    ):
        """Execute a custom error handler."""
        try:
            # Check if handler is async
            if inspect.iscoroutinefunction(handler):
                await handler(task, error, exception)
            else:
                handler(task, error, exception)
        except Exception as e:
            logger.error(f"Custom error handler failed: {e}")

    async def _execute_recovery_handlers(self, category: ErrorCategory, task: ProcessingTask, error: TaskError):
        """Execute recovery handlers for an error category."""
        handlers = self.recovery_handlers.get(category, [])
        
        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(task, error)
                else:
                    handler(task, error)
            except Exception as e:
                logger.error(f"Recovery handler failed: {e}")

    async def _check_alert_conditions(self, pattern: ErrorPattern, task: ProcessingTask, error: TaskError):
        """Check if alert conditions are met."""
        now = datetime.now()
        minute_key = now.strftime("%Y-%m-%d %H:%M")
        
        if minute_key not in self.error_stats:
            return
        
        stats = self.error_stats[minute_key]
        
        # Check error rate threshold
        if stats["total_errors"] > self.alert_thresholds["error_rate"]:
            await self._send_alert(
                "HIGH_ERROR_RATE",
                f"High error rate detected: {stats['total_errors']} errors in the last minute"
            )
        
        # Check pattern-specific thresholds
        pattern_count = stats["by_pattern"].get(pattern.name, 0)
        if pattern_count > 5:  # More than 5 errors of same pattern
            await self._send_alert(
                "PATTERN_THRESHOLD",
                f"High frequency of {pattern.name} errors: {pattern_count} in the last minute"
            )

    async def _send_alert(self, alert_type: str, message: str):
        """Send an alert (placeholder for actual alerting system)."""
        logger.error(f"ALERT [{alert_type}]: {message}")
        
        # In a real implementation, this would:
        # - Send notifications to administrators
        # - Update monitoring dashboards
        # - Trigger automated responses
        # - Log to external monitoring systems

    def add_recovery_handler(self, category: ErrorCategory, handler: Callable):
        """Add a recovery handler for an error category."""
        if category not in self.recovery_handlers:
            self.recovery_handlers[category] = []
        self.recovery_handlers[category].append(handler)

    def get_error_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        now = datetime.now()
        cutoff_time = now - timedelta(hours=hours)
        
        summary = {
            "total_errors": 0,
            "by_pattern": {},
            "by_category": {},
            "by_task_type": {},
            "time_period_hours": hours,
            "generated_at": now.isoformat()
        }
        
        for minute_key, stats in self.error_stats.items():
            minute_time = datetime.strptime(minute_key, "%Y-%m-%d %H:%M")
            
            if minute_time >= cutoff_time:
                summary["total_errors"] += stats["total_errors"]
                
                # Aggregate by pattern
                for pattern, count in stats["by_pattern"].items():
                    summary["by_pattern"][pattern] = summary["by_pattern"].get(pattern, 0) + count
                
                # Aggregate by category
                for category, count in stats["by_category"].items():
                    summary["by_category"][category] = summary["by_category"].get(category, 0) + count
                
                # Aggregate by task type
                for task_type, count in stats["by_task_type"].items():
                    summary["by_task_type"][task_type] = summary["by_task_type"].get(task_type, 0) + count
        
        return summary


# Global error handler instance
_error_handler: Optional[TaskErrorHandler] = None


def get_error_handler() -> TaskErrorHandler:
    """Get the global error handler instance."""
    global _error_handler
    
    if _error_handler is None:
        _error_handler = TaskErrorHandler()
    
    return _error_handler