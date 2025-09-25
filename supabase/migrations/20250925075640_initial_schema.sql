-- Initial schema migration
-- This migration consolidates all the Alembic migrations into a single Supabase migration

-- Create extension if not exists
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID NOT NULL PRIMARY KEY,
    telegram_id BIGINT,
    handle TEXT,
    locale TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create unique constraint for telegram_id (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_telegram_id_key'
    ) THEN
        ALTER TABLE public.users ADD CONSTRAINT users_telegram_id_key UNIQUE (telegram_id);
    END IF;
END $$;

-- Create photos table
CREATE TABLE IF NOT EXISTS public.photos (
    id UUID NOT NULL PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    tigris_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create estimates table
CREATE TABLE IF NOT EXISTS public.estimates (
    id UUID NOT NULL PRIMARY KEY,
    photo_id UUID REFERENCES public.photos(id) ON DELETE CASCADE,
    kcal_mean NUMERIC,
    kcal_min NUMERIC,
    kcal_max NUMERIC,
    items JSONB, -- renamed from breakdown
    confidence NUMERIC,
    status TEXT DEFAULT 'done',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create meals table
CREATE TABLE IF NOT EXISTS public.meals (
    id UUID NOT NULL PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    meal_date DATE NOT NULL,
    meal_type TEXT NOT NULL,
    kcal_total NUMERIC NOT NULL,
    source TEXT NOT NULL,
    estimate_id UUID REFERENCES public.estimates(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create goals table
CREATE TABLE IF NOT EXISTS public.goals (
    id UUID NOT NULL PRIMARY KEY,
    user_id UUID, -- nullable for testing, no foreign key constraint
    daily_kcal_target INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_photos_user_created ON public.photos (user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_meals_user_date ON public.meals (user_id, meal_date);
CREATE INDEX IF NOT EXISTS idx_estimates_photo_id ON public.estimates (photo_id);
CREATE INDEX IF NOT EXISTS idx_meals_estimate_id ON public.meals (estimate_id);
CREATE INDEX IF NOT EXISTS idx_goals_user_id ON public.goals (user_id);

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.estimates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.goals ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for users table
CREATE POLICY "Users can view own data" ON public.users
    FOR SELECT TO authenticated USING ((SELECT auth.uid())::text = id::text);

CREATE POLICY "Users can insert own data" ON public.users
    FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid())::text = id::text);

CREATE POLICY "Users can update own data" ON public.users
    FOR UPDATE TO authenticated USING ((SELECT auth.uid())::text = id::text);

CREATE POLICY "Users can delete own data" ON public.users
    FOR DELETE TO authenticated USING ((SELECT auth.uid())::text = id::text);

-- Create RLS policies for photos table
CREATE POLICY "Users can view own photos" ON public.photos
    FOR SELECT TO authenticated USING (
        user_id IN (
            SELECT id FROM public.users
            WHERE (SELECT auth.uid())::text = id::text
        )
    );

CREATE POLICY "Users can insert own photos" ON public.photos
    FOR INSERT TO authenticated WITH CHECK (
        user_id IN (
            SELECT id FROM public.users
            WHERE (SELECT auth.uid())::text = id::text
        )
    );

CREATE POLICY "Users can update own photos" ON public.photos
    FOR UPDATE TO authenticated USING (
        user_id IN (
            SELECT id FROM public.users
            WHERE (SELECT auth.uid())::text = id::text
        )
    );

CREATE POLICY "Users can delete own photos" ON public.photos
    FOR DELETE TO authenticated USING (
        user_id IN (
            SELECT id FROM public.users
            WHERE (SELECT auth.uid())::text = id::text
        )
    );

-- Create RLS policies for estimates table
CREATE POLICY "Users can view estimates for own photos" ON public.estimates
    FOR SELECT TO authenticated USING (
        photo_id IN (
            SELECT p.id FROM public.photos p
            JOIN public.users u ON p.user_id = u.id
            WHERE (SELECT auth.uid())::text = u.id::text
        )
    );

CREATE POLICY "Users can insert estimates for own photos" ON public.estimates
    FOR INSERT TO authenticated WITH CHECK (
        photo_id IN (
            SELECT p.id FROM public.photos p
            JOIN public.users u ON p.user_id = u.id
            WHERE (SELECT auth.uid())::text = u.id::text
        )
    );

CREATE POLICY "Users can update estimates for own photos" ON public.estimates
    FOR UPDATE TO authenticated USING (
        photo_id IN (
            SELECT p.id FROM public.photos p
            JOIN public.users u ON p.user_id = u.id
            WHERE (SELECT auth.uid())::text = u.id::text
        )
    );

CREATE POLICY "Users can delete estimates for own photos" ON public.estimates
    FOR DELETE TO authenticated USING (
        photo_id IN (
            SELECT p.id FROM public.photos p
            JOIN public.users u ON p.user_id = u.id
            WHERE (SELECT auth.uid())::text = u.id::text
        )
    );

-- Create RLS policies for meals table
CREATE POLICY "Users can view own meals" ON public.meals
    FOR SELECT TO authenticated USING (
        user_id IN (
            SELECT id FROM public.users
            WHERE (SELECT auth.uid())::text = id::text
        )
    );

CREATE POLICY "Users can insert own meals" ON public.meals
    FOR INSERT TO authenticated WITH CHECK (
        user_id IN (
            SELECT id FROM public.users
            WHERE (SELECT auth.uid())::text = id::text
        )
    );

CREATE POLICY "Users can update own meals" ON public.meals
    FOR UPDATE TO authenticated USING (
        user_id IN (
            SELECT id FROM public.users
            WHERE (SELECT auth.uid())::text = id::text
        )
    );

CREATE POLICY "Users can delete own meals" ON public.meals
    FOR DELETE TO authenticated USING (
        user_id IN (
            SELECT id FROM public.users
            WHERE (SELECT auth.uid())::text = id::text
        )
    );

-- Create RLS policies for goals table
CREATE POLICY "Users can view own goals" ON public.goals
    FOR SELECT TO authenticated USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can insert own goals" ON public.goals
    FOR INSERT TO authenticated WITH CHECK ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can update own goals" ON public.goals
    FOR UPDATE TO authenticated USING ((SELECT auth.uid()) = user_id);

CREATE POLICY "Users can delete own goals" ON public.goals
    FOR DELETE TO authenticated USING ((SELECT auth.uid()) = user_id);
