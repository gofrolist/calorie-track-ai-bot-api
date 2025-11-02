-- Enable Row Level Security on feedback_submissions table
-- Feature: 005-mini-app-improvements
--
-- Note: Access control is handled by the API layer (x-user-id header validation).
-- The backend uses service role key which bypasses RLS.
-- RLS is enabled for security best practices and defense-in-depth.

-- Enable RLS to satisfy Supabase security recommendations
ALTER TABLE public.feedback_submissions ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (service role bypasses RLS anyway)
-- No additional policies needed since API layer handles authentication
