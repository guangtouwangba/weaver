#!/usr/bin/env python
"""
ARQ Worker Entry Point.

This script starts the ARQ worker that processes background tasks from Redis.

Usage:
    # Direct execution
    python -m research_agent.worker.arq_main
    
    # Or via arq CLI
    arq research_agent.worker.arq_config.WorkerSettings
    
    # Or via start.sh with --worker flag
    ./start.sh --worker
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def main() -> None:
    """Start the ARQ worker."""
    from arq import run_worker
    
    from research_agent.config import get_settings
    from research_agent.shared.utils.logger import setup_logger
    from research_agent.worker.arq_config import WorkerSettings
    
    # Initialize logger
    logger = setup_logger(__name__)
    settings = get_settings()
    
    logger.info(f"🚀 Starting ARQ Worker")
    logger.info(f"   Environment: {settings.environment}")
    logger.info(f"   Redis URL: {settings.redis_url[:30]}..." if settings.redis_url else "   Redis URL: localhost (default)")
    logger.info(f"   Queue: arq:queue:{settings.environment}")
    logger.info(f"   Max concurrent jobs: {WorkerSettings.max_jobs}")
    logger.info(f"   Job timeout: {WorkerSettings.job_timeout}s")
    logger.info(f"   Max retries: {WorkerSettings.max_tries}")
    
    # Run the worker
    run_worker(WorkerSettings)


if __name__ == "__main__":
    main()





