#!/usr/bin/env python3
"""
Centralized logging configuration for the job scheduler system
Reduces HTTP library noise and provides clean output
"""

import logging
import sys
from typing import Optional

def setup_clean_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_str: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
):
    """
    Setup clean logging configuration with reduced HTTP library noise
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional log file path
        format_str: Log format string
    """
    # Setup handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=handlers
    )
    
    # Reduce noise from HTTP libraries and related components
    noisy_loggers = [
        'httpx',           # HTTP client library
        'httpcore',        # HTTP core components
        'urllib3',         # URL library
        'requests',        # HTTP requests library
        'h11',             # HTTP/1.1 protocol
        'hpack',           # HTTP/2 header compression
        'hyperframe',      # HTTP/2 framing
        'h2',              # HTTP/2 protocol
        'websockets',      # WebSocket library
        'asyncio',         # Async I/O library (can be noisy)
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Keep important loggers at appropriate levels
    logging.getLogger('supabase').setLevel(logging.INFO)
    logging.getLogger('database').setLevel(logging.INFO)
    logging.getLogger('jobs').setLevel(logging.INFO)


def get_clean_logger(name: str) -> logging.Logger:
    """Get a logger with clean configuration"""
    return logging.getLogger(name)