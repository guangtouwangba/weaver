"""
Base use case class.

Provides common functionality for all use cases.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseUseCase(ABC):
    """Base class for all use cases."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the use case."""
        pass
    
    def validate_input(self, data: Dict[str, Any], required_fields: list) -> None:
        """Validate input data has required fields."""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            from .exceptions import ValidationError
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def log_execution_start(self, operation: str, **kwargs) -> None:
        """Log the start of use case execution."""
        self.logger.info(f"Starting {operation}", extra=kwargs)
    
    def log_execution_end(self, operation: str, result: Any = None, **kwargs) -> None:
        """Log the end of use case execution."""
        self.logger.info(f"Completed {operation}", extra=kwargs)
    
    def log_error(self, operation: str, error: Exception, **kwargs) -> None:
        """Log an error during use case execution."""
        self.logger.error(f"Error in {operation}: {str(error)}", extra=kwargs, exc_info=True)