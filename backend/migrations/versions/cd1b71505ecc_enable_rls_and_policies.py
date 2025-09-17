"""enable_rls_and_policies

Revision ID: cd1b71505ecc
Revises: b3787d0bd8c7
Create Date: 2025-09-11 03:45:33.803265

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cd1b71505ecc"
down_revision: str | Sequence[str] | None = "b3787d0bd8c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable RLS and create policies for all tables."""

    # Enable RLS on all tables
    op.execute("ALTER TABLE public.users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.photos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.estimates ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.meals ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY")

    # Create policies for users table
    # Users can only see and modify their own records
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

    # Create policies for photos table
    # Users can only see photos they uploaded
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

    # Create policies for estimates table
    # Users can only see estimates for their photos
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

    # Create policies for meals table
    # Users can only see and modify their own meals
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

    # Create policy for alembic_version table
    # Only allow service role to access alembic_version
    op.execute("""
        CREATE POLICY "Service role can manage alembic_version" ON public.alembic_version
        FOR ALL USING (auth.role() = 'service_role')
    """)


def downgrade() -> None:
    """Disable RLS and drop policies."""

    # Drop all policies
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

    # Disable RLS on all tables
    op.execute("ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.meals DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.estimates DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.photos DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE public.users DISABLE ROW LEVEL SECURITY")
