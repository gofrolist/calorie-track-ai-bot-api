-- Migration: Add feedback submissions table
-- Feature: 005-mini-app-improvements
-- Date: 2025-11-01

BEGIN;

-- Create feedback_submissions table
CREATE TABLE IF NOT EXISTS feedback_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    message_type TEXT NOT NULL CHECK (message_type IN ('feedback', 'bug', 'question', 'support')),
    message_content TEXT NOT NULL CHECK (char_length(message_content) > 0 AND char_length(message_content) <= 5000),
    user_context JSONB,
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'reviewed', 'resolved')),
    admin_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for common query patterns
CREATE INDEX idx_feedback_user_id ON feedback_submissions(user_id);
CREATE INDEX idx_feedback_status ON feedback_submissions(status);
CREATE INDEX idx_feedback_created_at ON feedback_submissions(created_at DESC);
CREATE INDEX idx_feedback_type ON feedback_submissions(message_type);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_feedback_submissions_updated_at
    BEFORE UPDATE ON feedback_submissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant appropriate permissions (adjust based on your RLS policies)
-- ALTER TABLE feedback_submissions ENABLE ROW LEVEL SECURITY;

COMMIT;
