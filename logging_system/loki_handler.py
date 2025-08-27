"""
Grafana Loki Handler for Python Logging

Sends logs directly to Loki for centralized log aggregation and analysis.
"""

import json
import logging
import threading
import time
from datetime import datetime
from logging import LogRecord
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class LokiHandler(logging.Handler):
    """Handler that sends logs to Grafana Loki"""
    
    def __init__(
        self,
        url: str = "http://localhost:3100",
        labels: Optional[Dict[str, str]] = None,
        buffer_size: int = 100,
        flush_interval: float = 5.0,
        timeout: float = 10.0,
        max_retries: int = 3,
    ):
        super().__init__()
        
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required for LokiHandler")
        
        self.url = urljoin(url, "/loki/api/v1/push")
        self.labels = labels or {}
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Buffer for batching logs
        self.buffer = []
        self.buffer_lock = threading.Lock()
        self.last_flush = time.time()
        
        # HTTP client
        self.client = httpx.Client(timeout=self.timeout)
        
        # Background flush timer
        self.timer = None
        
    def emit(self, record: LogRecord):
        """Emit a log record to the buffer"""
        try:
            # Create log entry
            entry = self._create_log_entry(record)
            
            with self.buffer_lock:
                self.buffer.append(entry)
                
                # Check if we should flush
                should_flush = (
                    len(self.buffer) >= self.buffer_size or
                    time.time() - self.last_flush >= self.flush_interval
                )
                
                if should_flush:
                    self._flush_buffer()
                elif self.timer is None:
                    self._start_flush_timer()
                    
        except Exception:
            self.handleError(record)
    
    def _create_log_entry(self, record: LogRecord) -> Dict[str, Any]:
        """Create a Loki log entry from a log record"""
        # Base labels
        labels = self.labels.copy()
        
        # Add standard labels
        labels.update({
            "level": record.levelname.lower(),
            "logger": record.name,
            "module": getattr(record, 'module', 'unknown'),
            "function": getattr(record, 'funcName', 'unknown'),
        })
        
        # Add custom labels from record
        for attr in ['service', 'component', 'request_id', 'trace_id', 'span_id']:
            if hasattr(record, attr):
                labels[attr] = str(getattr(record, attr))
        
        # Create timestamp in nanoseconds
        timestamp_ns = str(int(record.created * 1_000_000_000))
        
        # Create log line (JSON format for structured logging)
        log_data = {
            "@timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None,
            }
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                'relativeCreated', 'thread', 'threadName', 'processName',
                'process', 'message', 'stack_info', 'exc_info', 'exc_text'
            ] and not key.startswith('_'):
                log_data[key] = value
        
        return {
            "timestamp": timestamp_ns,
            "line": json.dumps(log_data),
            "labels": labels
        }
    
    def _flush_buffer(self):
        """Flush the buffer to Loki"""
        if not self.buffer:
            return
        
        # Group entries by labels
        streams = {}
        for entry in self.buffer:
            # Create label string
            label_items = sorted(entry["labels"].items())
            label_str = "{" + ", ".join(f'{k}="{v}"' for k, v in label_items) + "}"
            
            if label_str not in streams:
                streams[label_str] = {
                    "stream": entry["labels"],
                    "values": []
                }
            
            streams[label_str]["values"].append([entry["timestamp"], entry["line"]])
        
        # Create Loki payload
        payload = {
            "streams": list(streams.values())
        }
        
        # Send to Loki
        self._send_to_loki(payload)
        
        # Clear buffer
        self.buffer.clear()
        self.last_flush = time.time()
        
        # Reset timer
        if self.timer:
            self.timer.cancel()
            self.timer = None
    
    def _send_to_loki(self, payload: Dict[str, Any]):
        """Send payload to Loki with retries"""
        for attempt in range(self.max_retries):
            try:
                response = self.client.post(
                    self.url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return  # Success
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Final attempt failed
                    import sys
                    sys.stderr.write(f"Failed to send logs to Loki after {self.max_retries} attempts: {e}\n")
                else:
                    # Exponential backoff
                    time.sleep(2 ** attempt)
    
    def _start_flush_timer(self):
        """Start the flush timer"""
        if self.timer is None:
            self.timer = threading.Timer(self.flush_interval, self._flush_buffer)
            self.timer.start()
    
    def flush(self):
        """Manually flush the buffer"""
        with self.buffer_lock:
            self._flush_buffer()
    
    def close(self):
        """Close the handler"""
        # Cancel timer
        if self.timer:
            self.timer.cancel()
        
        # Flush remaining logs
        with self.buffer_lock:
            self._flush_buffer()
        
        # Close HTTP client
        self.client.close()
        
        super().close()


class AsyncLokiHandler(LokiHandler):
    """Async version of LokiHandler using background thread"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Background worker thread
        self.worker_running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
    
    def _worker(self):
        """Background worker for flushing logs"""
        while self.worker_running:
            try:
                time.sleep(self.flush_interval)
                
                with self.buffer_lock:
                    if self.buffer and time.time() - self.last_flush >= self.flush_interval:
                        self._flush_buffer()
                        
            except Exception as e:
                import sys
                sys.stderr.write(f"AsyncLokiHandler worker error: {e}\n")
    
    def close(self):
        """Close the async handler"""
        # Stop worker thread
        self.worker_running = False
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        
        # Call parent close
        super().close()


def create_loki_handler(
    loki_url: str = "http://localhost:3100",
    service_name: str = "rag-system",
    environment: str = "development",
    **kwargs
) -> LokiHandler:
    """Factory function to create a Loki handler with common labels"""
    
    labels = {
        "service": service_name,
        "environment": environment,
        "job": service_name,
    }
    
    # Add any additional labels from kwargs
    labels.update(kwargs.pop("labels", {}))
    
    return LokiHandler(url=loki_url, labels=labels, **kwargs)