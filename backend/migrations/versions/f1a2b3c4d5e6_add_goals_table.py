"""add goals table

Revision ID: f1a2b3c4d5e6
Revises: ed68ca203ade
Create Date: 2025-09-20 18:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "ed68ca203ade"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create goals table
    op.create_table(
        "goals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("daily_kcal_target", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index for goals table
    op.create_index("idx_goals_user_id", "goals", ["user_id"])


def downgrade() -> None:
    # Drop index and table
    op.drop_index("idx_goals_user_id", table_name="goals")
    op.drop_table("goals")
