#!/usr/bin/env python3
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("import_check")

def check_import():
    """Attempt to import the main application."""

    # Add src to path if running from scripts dir
    current_dir = Path(__file__).resolve().parent
    src_dir = current_dir.parent / "src"

    if str(src_dir) not in sys.path:
        logger.info(f"Adding {src_dir} to sys.path")
        sys.path.insert(0, str(src_dir))

    try:
        logger.info("Attempting to import research_agent.main...")
        # We set environment variables to avoid database connection attempts during import
        # Use postgresql+asyncpg since that is the production driver (aiosqlite is dev-only)
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost:5432/dbname"
        os.environ["OPENROUTER_API_KEY"] = "sk-mock-key" # Mock key to pass validation

        from research_agent.main import app
        logger.info("Successfully imported research_agent.main")
        logger.info(f"App title: {app.title}")
        return True
    except ImportError as e:
        logger.error(f"ImportError: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        # Print stack trace
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Starting Production Import Check ===")
    if check_import():
        print("=== Import Check Passed ===")
        sys.exit(0)
    else:
        print("=== Import Check Failed ===")
        sys.exit(1)
