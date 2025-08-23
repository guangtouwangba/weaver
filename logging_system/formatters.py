"""
Log formatter module

Provides various log formatters supporting different output formats and scenarios.
"""

import json
import logging
import traceback
from datetime import datetime
from logging import LogRecord
from typing import Any, Dict, Optional

from logging_system.context import LogContext


class BaseFormatter(logging.Formatter):
    """Base formatter"""

    def __init__(
        self,
        include_context: bool = True,
        include_traceback: bool = True,
        sensitive_fields: list = None,
    ):
        super().__init__()
        self.include_context = include_context
        self.include_traceback = include_traceback
        self.sensitive_fields = sensitive_fields or []

    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize sensitive data"""
        if isinstance(data, dict):
            return {
                k: (
                    "***MASKED***"
                    if any(field in k.lower() for field in self.sensitive_fields)
                    else self._sanitize_data(v)
                )
                for k, v in data.items()
            }
        elif isinstance(data, (list, tuple)):
            return type(data)(self._sanitize_data(item) for item in data)
        return data

    def _get_context_data(self, record: LogRecord) -> Dict[str, Any]:
        """Get context data"""
        context = {}

        # Get current context
        if self.include_context:
            current_context = LogContext.get_current()
            if current_context:
                # Convert LogContext to dict
                context_dict = {
                    "request_id": current_context.request_id,
                    "correlation_id": current_context.correlation_id,
                    "session_id": current_context.session_id,
                    "user_id": current_context.user_id,
                    "operation": current_context.operation,
                    "component": current_context.component,
                    "service": current_context.service,
                    "started_at": (
                        current_context.started_at.isoformat()
                        if current_context.started_at
                        else None
                    ),
                }
                # Add non-null values
                context.update({k: v for k, v in context_dict.items() if v is not None})
                # Add extra fields
                if current_context.extra:
                    context.update(current_context.extra)

        # Get additional attributes from record
        extra_attrs = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "stack_info",
                "exc_info",
                "exc_text",
            ]:
                extra_attrs[key] = value

        if extra_attrs:
            context["extra"] = extra_attrs

        return self._sanitize_data(context)


class JSONFormatter(BaseFormatter):
    """JSON formatter"""

    def format(self, record: LogRecord) -> str:
        """Format as JSON"""
        # Basic log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }

        # Add context data
        context_data = self._get_context_data(record)
        if context_data:
            log_data["context"] = context_data

        # Add exception information
        if record.exc_info and self.include_traceback:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data, ensure_ascii=False, default=str)


class StructuredFormatter(BaseFormatter):
    """Structured formatter"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_format = (
            "{timestamp} | {level:<8} | {logger:<20} | {module}:{function}:{line} | "
            "{message}"
        )

    def format(self, record: LogRecord) -> str:
        """Format as structured text"""
        # Basic formatting
        formatted = self.base_format.format(
            timestamp=datetime.fromtimestamp(record.created).strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )[:-3],
            level=record.levelname,
            logger=record.name[:20],
            module=record.module,
            function=record.funcName,
            line=record.lineno,
            message=record.getMessage(),
        )

        # Add context information
        context_data = self._get_context_data(record)
        if context_data:
            context_str = json.dumps(context_data, ensure_ascii=False, default=str)
            formatted += f" | Context: {context_str}"

        # Add exception information
        if record.exc_info and self.include_traceback:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


class ColoredFormatter(BaseFormatter):
    """Colored console formatter"""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Purple
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self, use_colors: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors

    def format(self, record: LogRecord) -> str:
        """Format as colored text"""
        # Select color
        color = self.COLORS.get(record.levelname, "") if self.use_colors else ""
        reset = self.COLORS["RESET"] if self.use_colors else ""

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]

        # Basic formatting
        formatted = (
            f"{timestamp} {color}[{record.levelname:<8}]{reset} "
            f"{record.name:<20} | {record.module}:{record.funcName}:{record.lineno} | "
            f"{record.getMessage()}"
        )

        # Add context information (simplified display)
        context_data = self._get_context_data(record)
        if context_data and len(context_data) > 0:
            context_keys = list(context_data.keys())[:3]  # Only show first 3 keys
            context_summary = ", ".join(f"{k}={context_data[k]}" for k in context_keys)
            if len(context_data) > 3:
                context_summary += f" (+{len(context_data) - 3} more)"
            formatted += f" {color}[{context_summary}]{reset}"

        # Add exception information
        if record.exc_info and self.include_traceback:
            formatted += f"\n{color}" + self.formatException(record.exc_info) + reset

        return formatted


class RequestFormatter(BaseFormatter):
    """HTTP request specific formatter"""

    def format(self, record: LogRecord) -> str:
        """Format HTTP request logs"""
        # Basic formatting
        timestamp = datetime.fromtimestamp(record.created).isoformat()

        # Extract request-related information
        context_data = self._get_context_data(record)

        # Build request log format
        parts = [f"[{timestamp}]", f"[{record.levelname}]", f"[{record.name}]"]

        # Add HTTP-related information
        if context_data:
            if "request_id" in context_data:
                parts.append(f"[{context_data['request_id']}]")

            if "method" in context_data and "path" in context_data:
                parts.append(f"[{context_data['method']} {context_data['path']}]")

            if "user_id" in context_data:
                parts.append(f"[User:{context_data['user_id']}]")

            if "duration" in context_data:
                parts.append(f"[{context_data['duration']:.3f}s]")

        parts.append(record.getMessage())

        formatted = " ".join(parts)

        # Add exception information
        if record.exc_info and self.include_traceback:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


class CompactFormatter(BaseFormatter):
    """Compact formatter - for production environments"""

    def format(self, record: LogRecord) -> str:
        """Format as compact format"""
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")

        # Compact format
        formatted = f"{timestamp} {record.levelname[0]} {record.name.split('.')[-1]} {record.getMessage()}"

        # Only add exception info for errors
        if record.exc_info and record.levelno >= logging.ERROR:
            # Only show exception type and message, not full traceback
            exc_type = record.exc_info[0].__name__
            exc_msg = str(record.exc_info[1])
            formatted += f" [{exc_type}: {exc_msg}]"

        return formatted


# Formatter factory
def create_formatter(format_type: str, **kwargs) -> logging.Formatter:
    """Create formatter"""
    formatters = {
        "json": JSONFormatter,
        "structured": StructuredFormatter,
        "colored": ColoredFormatter,
        "request": RequestFormatter,
        "compact": CompactFormatter,
        "simple": CompactFormatter,
    }

    formatter_class = formatters.get(format_type.lower(), StructuredFormatter)
    return formatter_class(**kwargs)
