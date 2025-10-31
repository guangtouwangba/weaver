"""Basic logging configuration."""

import logging


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a simple formatter."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
