"""Logging configuration with Loki integration."""

import logging
import sys
from typing import Optional

from research_agent.config import get_settings


def setup_logger(name: Optional[str] = None) -> logging.Logger:
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
                from logging_loki import LokiQueueHandler

                loki_handler = LokiQueueHandler(
                    queue=-1,  # Use unbounded queue
                    url=settings.loki_url,
                    tags={"service": "backend", "environment": settings.environment},
                    version="1",
                )
                loki_handler.setLevel(getattr(logging, settings.log_level.upper()))
                logger.addHandler(loki_handler)
                logger.info(f"Loki handler initialized: {settings.loki_url}")
            except ImportError:
                logger.warning(
                    "python-logging-loki not installed. Loki logging disabled."
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Loki handler: {e}")

    return logger


# Default logger instance
logger = setup_logger()

