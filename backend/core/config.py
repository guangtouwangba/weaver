"""
Application configuration management.
"""
from functools import lru_cache
from config import Config

@lru_cache()
def get_settings():
    """Get application settings (cached)"""
    return Config