"""
Data Transfer Objects (DTOs) Package

This package contains all DTOs used throughout the application,
providing clear contracts for data exchange between layers.

Organization:
- fileupload/: File upload and management DTOs
"""

from . import fileupload

__all__ = [
    "fileupload"
]