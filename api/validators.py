"""
Input validation utilities for API endpoints.

This module provides validation functions for common input patterns
and business rules specific to the RAG system.
"""

import re
from typing import List, Optional, Dict, Any
from pathlib import Path

from api.exceptions import raise_validation_error


def validate_topic_name(name: str) -> None:
    """
    Validate topic name.
    
    Rules:
    - Must be between 1 and 255 characters
    - Cannot be only whitespace
    - Cannot contain certain special characters
    """
    if not name or not name.strip():
        raise_validation_error("name", "Topic name cannot be empty")
    
    if len(name) > 255:
        raise_validation_error("name", "Topic name cannot exceed 255 characters")
    
    # Check for invalid characters
    invalid_chars = ['<', '>', '"', '\'', '&', '\n', '\r', '\t']
    for char in invalid_chars:
        if char in name:
            raise_validation_error("name", f"Topic name cannot contain '{char}'")


def validate_topic_description(description: Optional[str]) -> None:
    """
    Validate topic description.
    
    Rules:
    - Cannot exceed 1000 characters
    - Cannot contain malicious content
    """
    if description is None:
        return
    
    if len(description) > 1000:
        raise_validation_error("description", "Description cannot exceed 1000 characters")
    
    # Check for potential script injection
    suspicious_patterns = [
        r'<script.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'eval\s*\(',
        r'Function\s*\('
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            raise_validation_error("description", "Description contains potentially unsafe content")


def validate_topic_category(category: Optional[str]) -> None:
    """
    Validate topic category.
    
    Rules:
    - Cannot exceed 50 characters
    - Must match allowed pattern
    """
    if category is None:
        return
    
    if len(category) > 50:
        raise_validation_error("category", "Category cannot exceed 50 characters")
    
    # Category should be alphanumeric with spaces, hyphens, and underscores
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', category):
        raise_validation_error(
            "category", 
            "Category can only contain letters, numbers, spaces, hyphens, and underscores"
        )


def validate_tag_names(tags: List[str]) -> None:
    """
    Validate tag names.
    
    Rules:
    - Each tag cannot exceed 50 characters
    - Tags must be unique
    - Tags cannot be empty
    - Cannot have more than 20 tags
    """
    if len(tags) > 20:
        raise_validation_error("tags", "Cannot have more than 20 tags")
    
    seen_tags = set()
    for tag in tags:
        if not tag or not tag.strip():
            raise_validation_error("tags", "Tag names cannot be empty")
        
        tag = tag.strip()
        if len(tag) > 50:
            raise_validation_error("tags", f"Tag '{tag}' exceeds 50 characters")
        
        if tag.lower() in seen_tags:
            raise_validation_error("tags", f"Duplicate tag: '{tag}'")
        
        seen_tags.add(tag.lower())
        
        # Tag should not contain special characters
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', tag):
            raise_validation_error(
                "tags", 
                f"Tag '{tag}' can only contain letters, numbers, spaces, hyphens, and underscores"
            )


def validate_file_upload(filename: str, file_size: int, content_type: Optional[str] = None) -> None:
    """
    Validate file upload.
    
    Rules:
    - File size limits
    - Allowed file extensions
    - Content type validation
    """
    # Maximum file size: 100MB
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    if file_size > MAX_FILE_SIZE:
        raise_validation_error(
            "file", 
            f"File size ({file_size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
        )
    
    # Get file extension
    file_path = Path(filename)
    extension = file_path.suffix.lower()
    
    # Allowed extensions
    ALLOWED_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.txt', '.md', '.rtf',  # Documents
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',  # Images
        '.mp3', '.wav', '.flac', '.ogg',  # Audio
        '.mp4', '.avi', '.mov', '.wmv', '.mkv',  # Video
        '.zip', '.rar', '.tar', '.gz', '.7z',  # Archives
        '.json', '.xml', '.csv', '.yaml', '.yml'  # Data
    }
    
    if extension not in ALLOWED_EXTENSIONS:
        raise_validation_error(
            "file", 
            f"File type '{extension}' is not allowed. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    
    # Validate content type if provided
    if content_type:
        # Basic content type validation
        suspicious_types = [
            'application/x-executable',
            'application/x-msdownload',
            'application/octet-stream',
            'text/html',
            'text/javascript'
        ]
        
        if content_type in suspicious_types:
            raise_validation_error("file", f"Content type '{content_type}' is not allowed")


def validate_search_query(query: str) -> None:
    """
    Validate search query.
    
    Rules:
    - Cannot be empty or only whitespace
    - Cannot exceed 500 characters
    - Cannot contain certain special characters
    """
    if not query or not query.strip():
        raise_validation_error("query", "Search query cannot be empty")
    
    if len(query) > 500:
        raise_validation_error("query", "Search query cannot exceed 500 characters")
    
    # Check for potential injection attempts
    suspicious_patterns = [
        r'<script.*?>',
        r'javascript:',
        r'SELECT\s+.*\s+FROM',
        r'DROP\s+TABLE',
        r'DELETE\s+FROM',
        r'INSERT\s+INTO',
        r'UPDATE\s+.*\s+SET'
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise_validation_error("query", "Search query contains potentially unsafe content")


def validate_pagination(limit: int, offset: int) -> None:
    """
    Validate pagination parameters.
    
    Rules:
    - Limit must be between 1 and 100
    - Offset must be non-negative
    - Offset cannot be unreasonably large
    """
    if limit < 1 or limit > 100:
        raise_validation_error("limit", "Limit must be between 1 and 100")
    
    if offset < 0:
        raise_validation_error("offset", "Offset cannot be negative")
    
    # Prevent unreasonably large offsets (could indicate an attack)
    if offset > 1000000:
        raise_validation_error("offset", "Offset is too large")


def validate_metadata(metadata: Dict[str, Any]) -> None:
    """
    Validate metadata dictionary.
    
    Rules:
    - Cannot have more than 50 key-value pairs
    - Keys cannot exceed 100 characters
    - Values cannot exceed 1000 characters when serialized
    - Cannot contain dangerous content
    """
    if len(metadata) > 50:
        raise_validation_error("metadata", "Metadata cannot have more than 50 key-value pairs")
    
    for key, value in metadata.items():
        if len(key) > 100:
            raise_validation_error("metadata", f"Metadata key '{key}' exceeds 100 characters")
        
        # Serialize value to check size
        import json
        try:
            value_str = json.dumps(value)
            if len(value_str) > 1000:
                raise_validation_error("metadata", f"Metadata value for key '{key}' is too large")
        except (TypeError, ValueError):
            raise_validation_error("metadata", f"Metadata value for key '{key}' is not JSON serializable")
        
        # Check for suspicious content in string values
        if isinstance(value, str):
            suspicious_patterns = [
                r'<script.*?>',
                r'javascript:',
                r'eval\s*\(',
                r'Function\s*\('
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    raise_validation_error("metadata", f"Metadata value for key '{key}' contains unsafe content")


def sanitize_input(text: str) -> str:
    """
    Sanitize text input by removing dangerous characters.
    
    This function should be used carefully and only when necessary,
    as it modifies user input.
    """
    if not text:
        return text
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove control characters except common whitespace
    import unicodedata
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\r\t ')
    
    # Trim whitespace
    text = text.strip()
    
    return text