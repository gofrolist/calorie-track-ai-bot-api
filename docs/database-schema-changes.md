# Database Schema Changes for Multi-Photo Meal Tracking

This document describes the database schema changes implemented for the multi-photo meal tracking feature (Feature: 003-update-logic-for).

## How Schema Changes Are Applied

There is no migration tool (no Alembic, no migrations directory) in the repository.

- The base schema lives in `backend/infra/schema.sql` (idempotent `create table if not exists ...`). It is applied manually against Neon, e.g. with `psql "$DATABASE_URL" -f backend/infra/schema.sql` or the Neon console SQL editor.
- Schema changes are applied by hand as SQL statements against the Neon database. Nothing runs them on deploy.
- The feature 003 changes below were originally applied by `supabase/migrations/20250930012519_multiphotos_meals.sql` and `supabase/migrations/20251002100414_add_photo_ids_to_estimates.sql`. The `supabase/` directory was deleted in commit `0222207` ("migrate from supabase to neon"); use `git show 0222207^:<path>` to view them.

`backend/infra/schema.sql` was regenerated from the live Neon schema on 2026-10-11 and includes the changes below, plus the `ui_configurations`, `inline_analytics_daily` and `feedback_submissions` tables and the `query_daily_statistics()` function. When you change the live schema, update `schema.sql` in the same PR.

## Overview

The schema changes extend the existing database to support:
- Multiple photos per meal (up to 5)
- Macronutrient tracking per meal
- Enhanced meal management with calendar views
- Better performance for photo and meal queries

## Table Changes

The definitions below reflect the live Neon database.

### 1. Photos Table

**New Fields Added**:
```sql
-- Meal the photo belongs to (set when a meal is created from an estimate)
meal_id UUID REFERENCES meals(id)

-- Telegram media group ID for grouped photos
media_group_id VARCHAR(255)

-- Display order for carousel (0-4)
display_order INTEGER DEFAULT 0 CHECK (display_order BETWEEN 0 AND 4)

-- Indexes for performance
CREATE INDEX idx_photos_meal_id ON photos(meal_id);
CREATE INDEX idx_photos_media_group ON photos(media_group_id);
```

**Purpose**:
- `meal_id`: Links photos to the meal created from their estimate
- `display_order`: Controls the order of photos in the carousel (0-indexed)
- `media_group_id`: Links photos that were uploaded together in Telegram
- Indexes: Improve query performance for meal photo retrieval

Note: the original migration declared `meal_id ... ON DELETE CASCADE`, but the live foreign key has no `ON DELETE` action.

### 2. Meals Table

**New Fields Added**:
```sql
-- Macronutrients
protein_grams NUMERIC CHECK (protein_grams >= 0)
carbs_grams   NUMERIC CHECK (carbs_grams >= 0)
fats_grams    NUMERIC CHECK (fats_grams >= 0)

-- Meal description
description TEXT

-- Confidence score for AI estimates (no CHECK constraint)
confidence_score NUMERIC

-- Last update timestamp
updated_at TIMESTAMPTZ DEFAULT now()

-- Indexes for performance
CREATE INDEX idx_meals_user_created ON meals(user_id, created_at DESC);
CREATE INDEX idx_meals_created_at ON meals(created_at);
```

**Purpose**:
- `protein_grams` / `carbs_grams` / `fats_grams`: Per-meal macros (from the estimate, or user overrides)
- `description`: Meal description (generated from estimate items when empty)
- `confidence_score`: Track AI estimation confidence
- Indexes: Optimize queries for user meal history and calendar views

`description`, `confidence_score` and `updated_at` are not in either historical migration file; they exist in the live database only.

### 3. Estimates Table

**New Fields Added**:
```sql
-- Macronutrient breakdown from the AI estimate
macronutrients JSONB

-- Number of photos in the estimate
photo_count INTEGER DEFAULT 1

-- Support for multi-photo estimates
photo_ids TEXT[] -- Array of photo IDs for multi-photo estimates

-- Index for array lookups
CREATE INDEX idx_estimates_photo_ids ON estimates USING GIN (photo_ids);
```

**Purpose**:
- `macronutrients`: Store protein/carbs/fats returned by the estimator
- `photo_count` / `photo_ids`: Support multiple photos in a single estimate
- Index: Improve estimate lookup by photo

## New Tables

Feature 003 added no new tables. Daily, weekly and monthly summaries are computed at query time from `meals` (`services/db/summaries.py`, and the `query_daily_statistics()` SQL function called by `services/statistics_service.py`, added by the 005 migration `20251102080000_add_macro_columns_to_meals.sql`); there is no `daily_summary` table.

## Migration Scripts

The original migration (`supabase/migrations/20250930012519_multiphotos_meals.sql`, abridged):

```sql
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

-- Step 7: Set display_order for existing photos
UPDATE photos SET display_order = 0 WHERE display_order IS NULL;
```

Follow-up (`supabase/migrations/20251002100414_add_photo_ids_to_estimates.sql`):

```sql
ALTER TABLE estimates
  ADD COLUMN IF NOT EXISTS photo_ids TEXT[] DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_estimates_photo_ids ON estimates USING GIN (photo_ids);

-- Backfill from the single photo_id column
UPDATE estimates
SET photo_ids = ARRAY[photo_id::TEXT]
WHERE photo_id IS NOT NULL AND photo_ids IS NULL;
```

## Data Integrity Constraints

### Photo Constraints
- Maximum 5 photos per meal (enforced by `display_order` constraint and the `photo_ids[:5]` slice in `services/db/meals.py`)
- Unique `display_order` per meal (enforced by application logic)
- Valid `display_order` range (0-4)

### Meal Constraints
- Non-negative macronutrient values (CHECK constraints)
- `confidence_score` range (0-1) is not enforced by the database

## Performance Optimizations

### Indexes Added
1. **Photos Table**:
   - `idx_photos_meal_id`: Fast meal photo retrieval
   - `idx_photos_media_group`: Media group queries

2. **Meals Table**:
   - `idx_meals_user_created`: User meal history queries
   - `idx_meals_created_at`: General meal queries

3. **Estimates Table**:
   - `idx_estimates_photo_ids`: GIN index on photo ID array

### Query Optimizations
- Efficient photo ordering with display_order
- Optimized meal history queries with proper indexing

## Backward Compatibility

### Existing Data
- All existing photos get `display_order = 0`
- Existing estimates get `photo_ids` backfilled from `photo_id`
- Existing meals remain unchanged (macro columns are NULL)
- No data loss during migration

### API Compatibility
- Existing API endpoints continue to work
- New fields are optional in responses
- Graceful handling of missing new fields (macros default to 0 in `services/db/meals.py`)

## Rollback Plan

### Rollback Steps
1. Drop new indexes
2. Remove new columns

### Rollback Scripts
```sql
-- Rollback photo_ids
DROP INDEX IF EXISTS idx_estimates_photo_ids;
ALTER TABLE estimates DROP COLUMN IF EXISTS photo_ids;

-- Rollback estimates changes
ALTER TABLE estimates DROP COLUMN IF EXISTS macronutrients;
ALTER TABLE estimates DROP COLUMN IF EXISTS photo_count;

-- Rollback photos changes
DROP INDEX IF EXISTS idx_photos_meal_id;
DROP INDEX IF EXISTS idx_photos_media_group;
ALTER TABLE photos DROP COLUMN IF EXISTS meal_id;
ALTER TABLE photos DROP COLUMN IF EXISTS media_group_id;
ALTER TABLE photos DROP COLUMN IF EXISTS display_order;

-- Rollback meals changes
DROP INDEX IF EXISTS idx_meals_user_created;
DROP INDEX IF EXISTS idx_meals_created_at;
ALTER TABLE meals DROP COLUMN IF EXISTS protein_grams;
ALTER TABLE meals DROP COLUMN IF EXISTS carbs_grams;
ALTER TABLE meals DROP COLUMN IF EXISTS fats_grams;
```

The current code depends on all of these columns, so a rollback also requires reverting the application.

## Monitoring and Maintenance

### Performance Monitoring
- Monitor query performance for new indexes
- Monitor photo storage usage

### Maintenance Tasks
- Regular index maintenance
- Photo storage optimization

### Data Validation
- Regular checks for data integrity
- Validation of display_order constraints
- Monitoring of confidence_score values

## Future Considerations

### Scalability
- Consider partitioning for large photo tables
- Implement photo archival for old meals
- Optimize storage for high-volume users

### Additional Features
- Photo compression and optimization
- Advanced calendar features
- Meal sharing and collaboration

### Performance Improvements
- Materialized views for complex queries
- Caching strategies for frequently accessed data
- Background processing for heavy operations
