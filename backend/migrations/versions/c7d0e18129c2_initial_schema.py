"""Initial schema

Revision ID: c7d0e18129c2
Revises:
Create Date: 2025-09-11 01:32:55.061267

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d0e18129c2"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create extension if not exists
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("handle", sa.Text(), nullable=True),
        sa.Column("locale", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )

    # Create photos table
    op.create_table(
        "photos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("tigris_key", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="uploaded"),
        sa.Column("meta", sa.JSON(), nullable=True, server_default="{}"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create estimates table
    op.create_table(
        "estimates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("photo_id", sa.UUID(), nullable=True),
        sa.Column("kcal_mean", sa.Numeric(), nullable=True),
        sa.Column("kcal_min", sa.Numeric(), nullable=True),
        sa.Column("kcal_max", sa.Numeric(), nullable=True),
        sa.Column("breakdown", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Numeric(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True, server_default="done"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["photo_id"], ["photos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create meals table
    op.create_table(
        "meals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("meal_date", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.Text(), nullable=False),
        sa.Column("kcal_total", sa.Numeric(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("estimate_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["estimate_id"], ["estimates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_photos_user_created", "photos", ["user_id", "created_at"])
    op.create_index("idx_meals_user_date", "meals", ["user_id", "meal_date"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index("idx_meals_user_date", table_name="meals")
    op.drop_index("idx_photos_user_created", table_name="photos")

    # Drop tables in reverse order
    op.drop_table("meals")
    op.drop_table("estimates")
    op.drop_table("photos")
    op.drop_table("users")

    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
