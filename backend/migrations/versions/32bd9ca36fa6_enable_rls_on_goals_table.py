"""enable_rls_on_goals_table

Revision ID: 32bd9ca36fa6
Revises: g2h3i4j5k6l7
Create Date: 2025-09-25 02:41:51.377642

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "32bd9ca36fa6"
down_revision: str | Sequence[str] | None = "g2h3i4j5k6l7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable RLS and create policies for goals table."""

    # Enable RLS on goals table
    op.execute("ALTER TABLE public.goals ENABLE ROW LEVEL SECURITY")

    # Create policies for goals table
    # Users can only see and modify their own goals
    op.execute("""
        CREATE POLICY "Users can view own goals" ON public.goals
        FOR SELECT USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can insert own goals" ON public.goals
        FOR INSERT WITH CHECK (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can update own goals" ON public.goals
        FOR UPDATE USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can delete own goals" ON public.goals
        FOR DELETE USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)


def downgrade() -> None:
    """Disable RLS and drop policies for goals table."""

    # Drop all policies for goals table
    op.execute('DROP POLICY IF EXISTS "Users can view own goals" ON public.goals')
    op.execute('DROP POLICY IF EXISTS "Users can insert own goals" ON public.goals')
    op.execute('DROP POLICY IF EXISTS "Users can update own goals" ON public.goals')
    op.execute('DROP POLICY IF EXISTS "Users can delete own goals" ON public.goals')

    # Disable RLS on goals table
    op.execute("ALTER TABLE public.goals DISABLE ROW LEVEL SECURITY")
