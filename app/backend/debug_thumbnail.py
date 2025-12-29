import asyncio
import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Default config
DB_URL = "postgresql+asyncpg://research_rag:research_rag_dev@localhost:5432/research_rag"


async def check_doc(doc_id):
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            text("SELECT id, thumbnail_path FROM documents WHERE id = :id"), {"id": doc_id}
        )
        row = result.fetchone()

        if not row:
            print(f"Document {doc_id} NOT FOUND in DB.")
            return

        print(f"Document ID: {row[0]}")
        path_str = row[1]
        print(f"Stored Path: '{path_str}'")

        if not path_str:
            print("Thumbnail path is NULL/Empty.")
            return

        path = Path(path_str)
        print(f"Resolved Path object: {path}")
        print(f"Is Absolute? {path.is_absolute()}")

        exists = path.exists()
        print(f"Does file exist? {exists}")

        if not exists:
            # Check parent permission
            print(f"Parent exists? {path.parent.exists()}")
            try:
                print(f"Listing parent {path.parent}:")
                for p in path.parent.glob("*.webp"):
                    print(f" - {p.name}")
            except Exception as e:
                print(f"Error listing parent: {e}")


if __name__ == "__main__":
    doc_id = "1eabc8ba-9be0-4fbf-850b-6d7c3804e972"
    asyncio.run(check_doc(doc_id))
