#!/usr/bin/env python3
"""Script to run database migrations."""

import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set working directory to the app directory
os.chdir("/app")


def main():
    """Run database migrations."""
    try:
        # Create alembic config
        config = Config("/app/alembic.ini")

        # Run the migration
        command.upgrade(config, "head")
        print("Database migrations completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
