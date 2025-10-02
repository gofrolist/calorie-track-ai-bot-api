-- Migration: Multi-Photo Meal Tracking & Enhanced Meals History
-- Feature: 003-update-logic-for
-- Date: 2025-09-30

-- Step 1: Add macronutrient columns to meals
ALTER TABLE meals
  ADD COLUMN IF NOT EXISTS protein_grams DECIMAL(6,2) CHECK (protein_grams >= 0),
  ADD COLUMN IF NOT EXISTS carbs_grams DECIMAL(6,2) CHECK (carbs_grams >= 0),
  ADD COLUMN IF NOT EXISTS fats_grams DECIMAL(6,2) CHECK (fats_grams >= 0);

-- Step 2: Extend photos table
ALTER TABLE photos
  ADD COLUMN IF NOT EXISTS meal_id UUID REFERENCES meals(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS media_group_id VARCHAR(255),
  ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0 CHECK (display_order BETWEEN 0 AND 4);

-- Step 3: Create indexes
CREATE INDEX idx_meals_user_created ON meals(user_id, created_at DESC);
CREATE INDEX idx_meals_created_at ON meals(created_at);
CREATE INDEX idx_photos_meal_id ON photos(meal_id);
CREATE INDEX idx_photos_media_group ON photos(media_group_id);

-- Step 4: Extend estimates table
ALTER TABLE estimates
  ADD COLUMN IF NOT EXISTS macronutrients JSONB,
  ADD COLUMN IF NOT EXISTS photo_count INTEGER DEFAULT 1;

-- Step 5: Extend daily_summary table (skip if table doesn't exist)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'daily_summary') THEN
        ALTER TABLE daily_summary
          ADD COLUMN IF NOT EXISTS total_protein_grams DECIMAL(8,2) DEFAULT 0,
          ADD COLUMN IF NOT EXISTS total_carbs_grams DECIMAL(8,2) DEFAULT 0,
          ADD COLUMN IF NOT EXISTS total_fats_grams DECIMAL(8,2) DEFAULT 0;
    END IF;
END $$;

-- Step 6: Backfill existing photos with meal_id (if estimate exists)
-- Skip this step if estimate_id column doesn't exist in photos table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'photos' AND column_name = 'estimate_id'
    ) THEN
        UPDATE photos p
        SET meal_id = (
          SELECT m.id FROM meals m WHERE m.estimate_id = p.estimate_id LIMIT 1
        )
        WHERE p.estimate_id IS NOT NULL;
    END IF;
END $$;

-- Step 7: Set display_order for existing photos
UPDATE photos p
SET display_order = 0
WHERE display_order IS NULL;
