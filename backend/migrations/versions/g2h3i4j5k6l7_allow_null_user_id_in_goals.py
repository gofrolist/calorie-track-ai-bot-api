"""allow null user_id in goals

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2025-09-20 19:08:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g2h3i4j5k6l7"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Make user_id nullable and remove foreign key constraint for testing
    op.alter_column("goals", "user_id", nullable=True)
    # Drop the foreign key constraint
    op.drop_constraint("goals_user_id_fkey", "goals", type_="foreignkey")


def downgrade() -> None:
    # Re-add foreign key constraint
    op.create_foreign_key(
        "goals_user_id_fkey", "goals", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    # Make user_id not nullable again
    op.alter_column("goals", "user_id", nullable=False)
