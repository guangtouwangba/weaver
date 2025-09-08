"""
Simple main entry point.

Minimal setup for the simplified RAG system.
"""

import uvicorn
from src_simple.api import create_app


def main():
    """Start the simplified RAG application."""
    app = create_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,  # Different port to avoid conflicts
        reload=True
    )


if __name__ == "__main__":
    main()