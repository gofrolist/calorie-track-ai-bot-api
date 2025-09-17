"""add_foreign_key_indexes

Revision ID: 5433ce9b3d46
Revises: cd1b71505ecc
Create Date: 2025-09-11 11:25:19.615284

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5433ce9b3d46"
down_revision: str | Sequence[str] | None = "cd1b71505ecc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add indexes for foreign keys to improve performance."""

    # Add index for estimates.photo_id foreign key
    op.create_index("idx_estimates_photo_id", "estimates", ["photo_id"])

    # Add index for meals.estimate_id foreign key
    op.create_index("idx_meals_estimate_id", "meals", ["estimate_id"])

    # Note: We're keeping the existing composite indexes for now
    # as they might be useful for specific query patterns:
    # - idx_photos_user_created: for queries filtering by user and ordering by created_at
    # - idx_meals_user_date: for queries filtering by user and meal_date
    #
    # If these continue to be unused, they can be removed in a future migration


def downgrade() -> None:
    """Remove foreign key indexes."""

    # Drop foreign key indexes
    op.drop_index("idx_meals_estimate_id", table_name="meals")
    op.drop_index("idx_estimates_photo_id", table_name="estimates")
