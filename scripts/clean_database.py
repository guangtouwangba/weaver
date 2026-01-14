#!/usr/bin/env python3
"""Clean database by dropping and recreating the public schema."""

import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse


def load_env():
    """Load environment variables from .env file."""
    # Try to find .env file in project root
    current = Path(__file__).resolve().parent
    for _ in range(5):  # Search up to 5 levels
        env_file = current / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        os.environ.setdefault(key.strip(), value)
            return
        current = current.parent


async def reset_database():
    """Drop and recreate the public schema."""
    try:
        import asyncpg
    except ImportError:
        print("Error: asyncpg not installed")
        sys.exit(1)

    # Load .env first
    load_env()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in environment or .env file")
        sys.exit(1)

    # Extract username from URL for GRANT statements
    parsed = urlparse(db_url)
    db_user = parsed.username or "postgres"

    print(f"Connecting to database (user: {db_user})...")

    try:
        conn = await asyncpg.connect(db_url)
        await conn.execute("DROP SCHEMA public CASCADE")
        await conn.execute("CREATE SCHEMA public")
        # Grant to the actual user from the connection URL
        await conn.execute(f"GRANT ALL ON SCHEMA public TO {db_user}")
        await conn.execute("GRANT ALL ON SCHEMA public TO public")
        await conn.close()
        print("✅ Database schema reset!")
    except Exception as e:
        print(f"❌ Failed to reset database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(reset_database())
