#!/usr/bin/env python
"""Script to clear rag_mode setting from database.

Run from app/backend directory:
    python scripts/clear_rag_mode_setting.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def main():
    from research_agent.infrastructure.database.models import UserSettingModel
    from research_agent.infrastructure.database.session import get_async_session_factory
    from sqlalchemy import delete, select

    session_factory = get_async_session_factory()
    async with session_factory() as session:
        # Check current rag_mode settings
        result = await session.execute(
            select(UserSettingModel).where(UserSettingModel.setting_key == "rag_mode")
        )
        settings = result.scalars().all()

        if not settings:
            print("No rag_mode settings found in database.")
            return

        print(f"Found {len(settings)} rag_mode setting(s) in database:")
        for s in settings:
            print(
                f"  - user_id={s.user_id}, setting_key={s.setting_key}, setting_value={s.setting_value}"
            )

        # Delete them
        confirm = input("\nDelete these settings? (y/N): ")
        if confirm.lower() == "y":
            await session.execute(
                delete(UserSettingModel).where(UserSettingModel.setting_key == "rag_mode")
            )
            await session.commit()
            print("Deleted rag_mode settings from database. Restart backend to use .env value.")
        else:
            print("Cancelled.")


if __name__ == "__main__":
    asyncio.run(main())
