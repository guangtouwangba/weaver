#!/usr/bin/env python3
"""
Automatically fix Alembic migration version mismatch.

This script:
1. Finds the last available migration file in the container
2. Updates the database alembic_version table to match using alembic stamp
3. Returns the revision ID for the startup script
"""

import subprocess
import sys
from pathlib import Path

# Add src to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir / "src"))

try:
    from alembic.config import Config
    from alembic.script import ScriptDirectory
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}", file=sys.stderr)
    sys.exit(1)


def get_available_revisions():
    """Get all available revision IDs from migration files."""
    try:
        alembic_ini = backend_dir / "alembic.ini"
        config = Config(str(alembic_ini))
        script = ScriptDirectory.from_config(config)

        # Get all revisions in order
        revisions = []
        for rev in script.walk_revisions():
            revisions.append(rev.revision)

        return revisions
    except Exception as e:
        print(f"ERROR: Failed to get available revisions: {e}", file=sys.stderr)
        return []


def get_database_revision():
    """Get current revision from database using alembic current."""
    try:
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(backend_dir)
        )

        if result.returncode == 0 and result.stdout.strip():
            # Parse output: "20241204_000001 (head)" -> "20241204_000001"
            output = result.stdout.strip().split()[0]
            return output if output and output != "(empty)" else None
        return None
    except Exception as e:
        print(f"INFO: Could not get database revision: {e}", file=sys.stderr)
        return None


def set_database_revision(revision):
    """Set database revision using alembic stamp command."""
    try:
        result = subprocess.run(
            ["alembic", "stamp", revision],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(backend_dir)
        )

        if result.returncode != 0:
            print(f"ERROR: alembic stamp failed: {result.stderr}", file=sys.stderr)
            return False

        return True
    except Exception as e:
        print(f"ERROR: Failed to set database revision: {e}", file=sys.stderr)
        return False


def main():
    """Main function to auto-fix migration version."""
    # Get available revisions
    available_revisions = get_available_revisions()

    if not available_revisions:
        print("ERROR: No migration files found", file=sys.stderr)
        sys.exit(1)

    # Get the last available revision (head)
    # walk_revisions returns revisions from head to base, so first is head
    last_revision = available_revisions[0] if available_revisions else None

    if not last_revision:
        print("ERROR: No migration files found", file=sys.stderr)
        sys.exit(1)

    # Get current database revision
    db_revision = get_database_revision()

    # Determine target revision:
    # - If DB revision exists and is in available list, keep it (might be older but valid)
    # - If DB revision doesn't exist or is not in available list, use last available (head)
    if db_revision and db_revision in available_revisions:
        # Database has a valid revision that exists in container
        target_revision = db_revision
        print(f"INFO: Database revision {db_revision} is valid and exists in container", file=sys.stderr)
    else:
        # Database revision is missing or doesn't exist in container
        # Set to the last available revision (head) to ensure consistency
        target_revision = last_revision
        if db_revision:
            print(f"WARN: Database revision {db_revision} not found in available migrations", file=sys.stderr)
            print(f"INFO: Auto-fixing to last available revision: {target_revision}", file=sys.stderr)
        else:
            print(f"INFO: No database revision found, setting to: {target_revision}", file=sys.stderr)

    # Set database revision
    if set_database_revision(target_revision):
        print(target_revision)  # Output revision for shell script
        sys.exit(0)
    else:
        print("ERROR: Failed to update database revision", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

