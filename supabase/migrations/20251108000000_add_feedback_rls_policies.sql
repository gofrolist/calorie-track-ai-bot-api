-- Add RLS policies for feedback_submissions table
-- Feature: 005-mini-app-improvements
-- Date: 2025-11-08
--
-- This migration adds proper RLS policies for the feedback_submissions table.
-- While the backend uses service role key (which bypasses RLS), these policies
-- provide defense-in-depth security and satisfy Supabase security recommendations.

BEGIN;

-- Policy 1: Service role has full access (explicitly documented, though service role bypasses RLS)
-- This policy won't be evaluated for service role, but documents the intended access pattern
CREATE POLICY "Service role full access" ON public.feedback_submissions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy 2: Authenticated users can insert their own feedback
-- This allows direct client-side submission if needed in the future
CREATE POLICY "Users can submit their own feedback" ON public.feedback_submissions
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid()::text);

-- Policy 3: Authenticated users can view their own feedback
-- This allows users to see their submission history
CREATE POLICY "Users can view their own feedback" ON public.feedback_submissions
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid()::text);

-- Policy 4: Deny all access to anonymous users
-- Anonymous users cannot access feedback submissions
-- (This is the default behavior, but we make it explicit for clarity)

COMMIT;
