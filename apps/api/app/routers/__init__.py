"""Router package exposing API blueprints."""

from . import ingest, qa, search  # noqa: F401

__all__ = ["ingest", "qa", "search"]
