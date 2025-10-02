-- Migration: Multi-Photo Meal Tracking & Enhanced Meals History
-- Feature: 003-update-logic-for
-- Date: 2025-09-30

-- Step 1: Add macronutrient columns to meals
ALTER TABLE meals
  ADD COLUMN protein_grams DECIMAL(6,2) CHECK (protein_grams >= 0),
  ADD COLUMN carbs_grams DECIMAL(6,2) CHECK (carbs_grams >= 0),
  ADD COLUMN fats_grams DECIMAL(6,2) CHECK (fats_grams >= 0);

-- Step 2: Extend photos table
ALTER TABLE photos
  ADD COLUMN meal_id UUID REFERENCES meals(id) ON DELETE CASCADE,
  ADD COLUMN media_group_id VARCHAR(255),
  ADD COLUMN display_order INTEGER DEFAULT 0 CHECK (display_order BETWEEN 0 AND 4);

-- Step 3: Create indexes
CREATE INDEX idx_meals_user_created ON meals(user_id, created_at DESC);
CREATE INDEX idx_meals_created_at ON meals(created_at);
CREATE INDEX idx_photos_meal_id ON photos(meal_id);
CREATE INDEX idx_photos_media_group ON photos(media_group_id);

-- Step 4: Extend estimates table
ALTER TABLE estimates
  ADD COLUMN macronutrients JSONB,
  ADD COLUMN photo_count INTEGER DEFAULT 1;

-- Step 5: Extend daily_summary table
ALTER TABLE daily_summary
  ADD COLUMN total_protein_grams DECIMAL(8,2) DEFAULT 0,
  ADD COLUMN total_carbs_grams DECIMAL(8,2) DEFAULT 0,
  ADD COLUMN total_fats_grams DECIMAL(8,2) DEFAULT 0;

-- Step 6: Backfill existing photos with meal_id (if estimate exists)
UPDATE photos p
SET meal_id = (
  SELECT m.id FROM meals m WHERE m.estimate_id = p.estimate_id LIMIT 1
)
WHERE p.estimate_id IS NOT NULL;

-- Step 7: Set display_order for existing photos
UPDATE photos p
SET display_order = 0
WHERE display_order IS NULL;
