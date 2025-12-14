#!/usr/bin/env python3
"""Get the latest Alembic revision ID."""

import sys
from pathlib import Path

# Add src to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from alembic import command
from alembic.config import Config

# Load alembic config
alembic_ini = backend_dir / "alembic.ini"
config = Config(str(alembic_ini))

# Get current head revision
from alembic.script import ScriptDirectory
script = ScriptDirectory.from_config(config)
head = script.get_current_head()

print(head if head else "")

