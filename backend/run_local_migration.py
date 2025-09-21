#!/usr/bin/env python3
"""Script to run database migrations locally."""

import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Run database migrations."""
    try:
        # Create alembic config
        config = Config("alembic.ini")

        # Set the working directory to the backend directory
        os.chdir(str(Path(__file__).parent))

        print("Running database migrations...")

        # Run the migration
        command.upgrade(config, "head")
        print("Database migrations completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
