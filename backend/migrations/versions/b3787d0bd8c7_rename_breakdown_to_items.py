"""rename_breakdown_to_items

Revision ID: b3787d0bd8c7
Revises: c7d0e18129c2
Create Date: 2025-09-11 03:19:44.742292

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3787d0bd8c7"
down_revision: str | Sequence[str] | None = "c7d0e18129c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename breakdown column to items in estimates table
    op.alter_column("estimates", "breakdown", new_column_name="items")


def downgrade() -> None:
    """Downgrade schema."""
    # Rename items column back to breakdown in estimates table
    op.alter_column("estimates", "items", new_column_name="breakdown")
