"""optimize_rls_policies_performance

Revision ID: ed68ca203ade
Revises: 5433ce9b3d46
Create Date: 2025-09-11 12:02:53.102429

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ed68ca203ade"
down_revision: str | Sequence[str] | None = "5433ce9b3d46"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Optimize RLS policies for better performance by wrapping auth functions with SELECT."""

    # Drop existing policies
    op.execute('DROP POLICY IF EXISTS "Users can view own data" ON public.users')
    op.execute('DROP POLICY IF EXISTS "Users can insert own data" ON public.users')
    op.execute('DROP POLICY IF EXISTS "Users can update own data" ON public.users')
    op.execute('DROP POLICY IF EXISTS "Users can delete own data" ON public.users')

    op.execute('DROP POLICY IF EXISTS "Users can view own photos" ON public.photos')
    op.execute('DROP POLICY IF EXISTS "Users can insert own photos" ON public.photos')
    op.execute('DROP POLICY IF EXISTS "Users can update own photos" ON public.photos')
    op.execute('DROP POLICY IF EXISTS "Users can delete own photos" ON public.photos')

    op.execute(
        'DROP POLICY IF EXISTS "Users can view estimates for own photos" ON public.estimates'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Users can insert estimates for own photos" ON public.estimates'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Users can update estimates for own photos" ON public.estimates'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Users can delete estimates for own photos" ON public.estimates'
    )

    op.execute('DROP POLICY IF EXISTS "Users can view own meals" ON public.meals')
    op.execute('DROP POLICY IF EXISTS "Users can insert own meals" ON public.meals')
    op.execute('DROP POLICY IF EXISTS "Users can update own meals" ON public.meals')
    op.execute('DROP POLICY IF EXISTS "Users can delete own meals" ON public.meals')

    op.execute(
        'DROP POLICY IF EXISTS "Service role can manage alembic_version" ON public.alembic_version'
    )

    # Create optimized policies for users table
    op.execute("""
        CREATE POLICY "Users can view own data" ON public.users
        FOR SELECT USING ((select auth.uid())::text = id::text)
    """)
    op.execute("""
        CREATE POLICY "Users can insert own data" ON public.users
        FOR INSERT WITH CHECK ((select auth.uid())::text = id::text)
    """)
    op.execute("""
        CREATE POLICY "Users can update own data" ON public.users
        FOR UPDATE USING ((select auth.uid())::text = id::text)
    """)
    op.execute("""
        CREATE POLICY "Users can delete own data" ON public.users
        FOR DELETE USING ((select auth.uid())::text = id::text)
    """)

    # Create optimized policies for photos table
    op.execute("""
        CREATE POLICY "Users can view own photos" ON public.photos
        FOR SELECT USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE (select auth.uid())::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can insert own photos" ON public.photos
        FOR INSERT WITH CHECK (
            user_id IN (
                SELECT id FROM public.users
                WHERE (select auth.uid())::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can update own photos" ON public.photos
        FOR UPDATE USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE (select auth.uid())::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can delete own photos" ON public.photos
        FOR DELETE USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE (select auth.uid())::text = id::text
            )
        )
    """)

    # Create optimized policies for estimates table
    op.execute("""
        CREATE POLICY "Users can view estimates for own photos" ON public.estimates
        FOR SELECT USING (
            photo_id IN (
                SELECT p.id FROM public.photos p
                JOIN public.users u ON p.user_id = u.id
                WHERE (select auth.uid())::text = u.id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can insert estimates for own photos" ON public.estimates
        FOR INSERT WITH CHECK (
            photo_id IN (
                SELECT p.id FROM public.photos p
                JOIN public.users u ON p.user_id = u.id
                WHERE (select auth.uid())::text = u.id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can update estimates for own photos" ON public.estimates
        FOR UPDATE USING (
            photo_id IN (
                SELECT p.id FROM public.photos p
                JOIN public.users u ON p.user_id = u.id
                WHERE (select auth.uid())::text = u.id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can delete estimates for own photos" ON public.estimates
        FOR DELETE USING (
            photo_id IN (
                SELECT p.id FROM public.photos p
                JOIN public.users u ON p.user_id = u.id
                WHERE (select auth.uid())::text = u.id::text
            )
        )
    """)

    # Create optimized policies for meals table
    op.execute("""
        CREATE POLICY "Users can view own meals" ON public.meals
        FOR SELECT USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE (select auth.uid())::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can insert own meals" ON public.meals
        FOR INSERT WITH CHECK (
            user_id IN (
                SELECT id FROM public.users
                WHERE (select auth.uid())::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can update own meals" ON public.meals
        FOR UPDATE USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE (select auth.uid())::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can delete own meals" ON public.meals
        FOR DELETE USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE (select auth.uid())::text = id::text
            )
        )
    """)

    # Create optimized policy for alembic_version table
    op.execute("""
        CREATE POLICY "Service role can manage alembic_version" ON public.alembic_version
        FOR ALL USING ((select auth.role()) = 'service_role')
    """)


def downgrade() -> None:
    """Revert to original RLS policies (non-optimized)."""

    # Drop optimized policies
    op.execute('DROP POLICY IF EXISTS "Users can view own data" ON public.users')
    op.execute('DROP POLICY IF EXISTS "Users can insert own data" ON public.users')
    op.execute('DROP POLICY IF EXISTS "Users can update own data" ON public.users')
    op.execute('DROP POLICY IF EXISTS "Users can delete own data" ON public.users')

    op.execute('DROP POLICY IF EXISTS "Users can view own photos" ON public.photos')
    op.execute('DROP POLICY IF EXISTS "Users can insert own photos" ON public.photos')
    op.execute('DROP POLICY IF EXISTS "Users can update own photos" ON public.photos')
    op.execute('DROP POLICY IF EXISTS "Users can delete own photos" ON public.photos')

    op.execute(
        'DROP POLICY IF EXISTS "Users can view estimates for own photos" ON public.estimates'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Users can insert estimates for own photos" ON public.estimates'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Users can update estimates for own photos" ON public.estimates'
    )
    op.execute(
        'DROP POLICY IF EXISTS "Users can delete estimates for own photos" ON public.estimates'
    )

    op.execute('DROP POLICY IF EXISTS "Users can view own meals" ON public.meals')
    op.execute('DROP POLICY IF EXISTS "Users can insert own meals" ON public.meals')
    op.execute('DROP POLICY IF EXISTS "Users can update own meals" ON public.meals')
    op.execute('DROP POLICY IF EXISTS "Users can delete own meals" ON public.meals')

    op.execute(
        'DROP POLICY IF EXISTS "Service role can manage alembic_version" ON public.alembic_version'
    )

    # Recreate original policies (non-optimized)
    op.execute("""
        CREATE POLICY "Users can view own data" ON public.users
        FOR SELECT USING (auth.uid()::text = id::text)
    """)
    op.execute("""
        CREATE POLICY "Users can insert own data" ON public.users
        FOR INSERT WITH CHECK (auth.uid()::text = id::text)
    """)
    op.execute("""
        CREATE POLICY "Users can update own data" ON public.users
        FOR UPDATE USING (auth.uid()::text = id::text)
    """)
    op.execute("""
        CREATE POLICY "Users can delete own data" ON public.users
        FOR DELETE USING (auth.uid()::text = id::text)
    """)

    op.execute("""
        CREATE POLICY "Users can view own photos" ON public.photos
        FOR SELECT USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can insert own photos" ON public.photos
        FOR INSERT WITH CHECK (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can update own photos" ON public.photos
        FOR UPDATE USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can delete own photos" ON public.photos
        FOR DELETE USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)

    op.execute("""
        CREATE POLICY "Users can view estimates for own photos" ON public.estimates
        FOR SELECT USING (
            photo_id IN (
                SELECT p.id FROM public.photos p
                JOIN public.users u ON p.user_id = u.id
                WHERE auth.uid()::text = u.id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can insert estimates for own photos" ON public.estimates
        FOR INSERT WITH CHECK (
            photo_id IN (
                SELECT p.id FROM public.photos p
                JOIN public.users u ON p.user_id = u.id
                WHERE auth.uid()::text = u.id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can update estimates for own photos" ON public.estimates
        FOR UPDATE USING (
            photo_id IN (
                SELECT p.id FROM public.photos p
                JOIN public.users u ON p.user_id = u.id
                WHERE auth.uid()::text = u.id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can delete estimates for own photos" ON public.estimates
        FOR DELETE USING (
            photo_id IN (
                SELECT p.id FROM public.photos p
                JOIN public.users u ON p.user_id = u.id
                WHERE auth.uid()::text = u.id::text
            )
        )
    """)

    op.execute("""
        CREATE POLICY "Users can view own meals" ON public.meals
        FOR SELECT USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can insert own meals" ON public.meals
        FOR INSERT WITH CHECK (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can update own meals" ON public.meals
        FOR UPDATE USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)
    op.execute("""
        CREATE POLICY "Users can delete own meals" ON public.meals
        FOR DELETE USING (
            user_id IN (
                SELECT id FROM public.users
                WHERE auth.uid()::text = id::text
            )
        )
    """)

    op.execute("""
        CREATE POLICY "Service role can manage alembic_version" ON public.alembic_version
        FOR ALL USING (auth.role() = 'service_role')
    """)
