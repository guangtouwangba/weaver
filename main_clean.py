"""
Main entry point for the Clean Architecture RAG application.

This is a new main entry point that uses the refactored Clean Architecture.
"""

import uvicorn
from src.presentation.api.app_factory import create_app
from src.infrastructure.config.config_manager import get_config


def main():
    """Main function to start the application."""
    # Load configuration
    config = get_config()
    
    # Create FastAPI app
    app = create_app()
    
    # Run the application
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=config.debug,
        log_level=config.log_level.lower()
    )


if __name__ == "__main__":
    main()