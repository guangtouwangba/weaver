"""Logging configuration with Loki integration."""

import logging
import sys

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from research_agent.config import get_settings


class SafeLokiHandler(logging.Handler):
    """Loki handler with timeout and error handling to prevent blocking."""

    def __init__(self, url: str, tags: dict, timeout: float = 2.0):
        """Initialize safe Loki handler with timeout.

        Args:
            url: Loki push endpoint URL
            tags: Labels/tags for logs
            timeout: Request timeout in seconds (default: 2.0)
        """
        super().__init__()
        self.url = url
        self.tags = tags
        self.timeout = timeout

        # Create session with retry strategy and timeout
        self.session = requests.Session()

        # Configure retry strategy (max 1 retry, total timeout < 2s)
        retry_strategy = Retry(
            total=1,  # Only 1 retry attempt
            backoff_factor=0.1,  # Very short backoff
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=1,
            pool_maxsize=1,
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to Loki with timeout protection."""
        try:
            # Format log message
            message = self.format(record)

            # Prepare payload
            payload = {
                "streams": [
                    {
                        "stream": self.tags,
                        "values": [[str(int(record.created * 1e9)), message]],
                    }
                ]
            }

            # Send with timeout - this will raise TimeoutError if it takes too long
            response = self.session.post(
                self.url,
                json=payload,
                timeout=self.timeout,  # ✅ Critical: Set timeout
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

        except requests.exceptions.Timeout:
            # ✅ Silently ignore timeout - don't block application
            pass
        except requests.exceptions.ConnectionError:
            # ✅ Silently ignore connection errors - don't block application
            pass
        except requests.exceptions.RequestException:
            # ✅ Silently ignore all request errors - don't block application
            pass
        except Exception:
            # ✅ Silently ignore any other errors - don't block application
            # We don't want logging failures to crash the app
            self.handleError(record)


def setup_logger(name: str | None = None) -> logging.Logger:
    """Set up and return a logger instance with optional Loki handler."""
    settings = get_settings()

    logger = logging.getLogger(name or "research_agent")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    if not logger.handlers:
        # Console handler (always present for stdout/stderr)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, settings.log_level.upper()))

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Loki handler (optional, based on configuration)
        if settings.loki_enabled and settings.loki_url:
            try:
                # ✅ Use custom SafeLokiHandler with timeout protection
                loki_handler = SafeLokiHandler(
                    url=settings.loki_url,
                    tags={"service": "backend", "environment": settings.environment},
                    timeout=2.0,  # 2 second timeout - fast fail
                )
                loki_handler.setLevel(getattr(logging, settings.log_level.upper()))
                loki_handler.setFormatter(formatter)
                logger.addHandler(loki_handler)
                logger.info(
                    f"✅ Loki handler initialized with timeout protection: {settings.loki_url}"
                )
            except ImportError:
                logger.warning("python-logging-loki not installed. Loki logging disabled.")
            except Exception as e:
                logger.warning(f"Failed to initialize Loki handler: {e}")

    return logger


# Default logger instance
logger = setup_logger()
