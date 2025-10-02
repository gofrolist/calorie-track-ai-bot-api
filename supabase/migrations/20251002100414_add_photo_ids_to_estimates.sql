-- Migration: Add photo_ids column to estimates table
-- Feature: 003-update-logic-for (Multi-photo support)
-- Date: 2025-10-02

-- Add photo_ids column to estimates table to support multi-photo estimates
ALTER TABLE estimates
  ADD COLUMN IF NOT EXISTS photo_ids TEXT[] DEFAULT NULL;

-- Add index for photo_ids array column for better query performance
CREATE INDEX IF NOT EXISTS idx_estimates_photo_ids ON estimates USING GIN (photo_ids);

-- Update existing estimates to populate photo_ids from photo_id
UPDATE estimates
SET photo_ids = ARRAY[photo_id::TEXT]
WHERE photo_id IS NOT NULL AND photo_ids IS NULL;
