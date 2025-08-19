"""
Database models package.

This module provides SQLAlchemy ORM models for the RAG system.
"""

from sqlalchemy.ext.declarative import declarative_base

# Create declarative base for all models
Base = declarative_base()


def get_all_models():
    """Get all database models for Alembic migrations."""
    # Import all models here to ensure they are registered
    try:
        from . import base, topic, file, document
        return [
            base,
            topic, 
            file,
            document
        ]
    except ImportError:
        # If some models don't exist, return empty list
        return []


# Re-export Base for convenience
__all__ = ["Base", "get_all_models"]