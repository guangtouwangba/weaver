#!/usr/bin/env python3
"""Script to manually reprocess a document."""

import asyncio
import sys
from pathlib import Path

# Add backend src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uuid import UUID


async def main():
    from research_agent.infrastructure.database.session import get_async_session
    from research_agent.worker.tasks.document_processor import DocumentProcessorTask
    from research_agent.shared.utils.logger import logger

    document_id = UUID("0fb2e133-354c-4cec-9ae4-2bb96610fa3a")
    project_id = UUID("2d604d5f-93a4-4125-bca8-9daec9b24490")
    # Use path starting with upload_dir format (./data/uploads/...)
    file_path = "./data/uploads/projects/2d604d5f-93a4-4125-bca8-9daec9b24490/0fb2e133-354c-4cec-9ae4-2bb96610fa3a.pdf"

    payload = {
        "document_id": str(document_id),
        "project_id": str(project_id),
        "file_path": file_path,
    }

    logger.info(f"Starting manual document reprocessing: {document_id}")

    task = DocumentProcessorTask()
    async with get_async_session() as session:
        await task.execute(payload, session)
        await session.commit()

    logger.info("Document reprocessing completed!")


if __name__ == "__main__":
    asyncio.run(main())

