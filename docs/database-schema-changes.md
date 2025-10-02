# Database Schema Changes for Multi-Photo Meal Tracking

This document describes the database schema changes implemented for the multi-photo meal tracking feature (Feature: 003-update-logic-for).

## Overview

The schema changes extend the existing database to support:
- Multiple photos per meal (up to 5)
- Enhanced meal management with calendar views
- Improved data relationships and constraints
- Better performance for photo and meal queries

## Table Changes

### 1. Photos Table

**New Fields Added**:
```sql
-- Display order for carousel (0-4)
display_order INTEGER NOT NULL DEFAULT 0 CHECK (display_order >= 0 AND display_order <= 4)

-- Telegram media group ID for grouped photos
media_group_id TEXT

-- Indexes for performance
CREATE INDEX idx_photos_meal_id ON photos(meal_id);
CREATE INDEX idx_photos_media_group_id ON photos(media_group_id);
CREATE INDEX idx_photos_display_order ON photos(meal_id, display_order);
```

**Purpose**:
- `display_order`: Controls the order of photos in the carousel (0-indexed)
- `media_group_id`: Links photos that were uploaded together in Telegram
- Indexes: Improve query performance for meal photo retrieval

### 2. Meals Table

**New Fields Added**:
```sql
-- Enhanced description field
description TEXT -- Increased from VARCHAR(255) to TEXT for longer descriptions

-- Confidence score for AI estimates
confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1)

-- Indexes for performance
CREATE INDEX idx_meals_user_id_created_at ON meals(user_id, created_at DESC);
CREATE INDEX idx_meals_created_at ON meals(created_at DESC);
```

**Purpose**:
- `description`: Support for longer meal descriptions
- `confidence_score`: Track AI estimation confidence
- Indexes: Optimize queries for user meal history and calendar views

### 3. Estimates Table

**New Fields Added**:
```sql
-- Support for multi-photo estimates
photo_ids TEXT[] -- Array of photo IDs for multi-photo estimates

-- Media group tracking
media_group_id TEXT

-- Enhanced description
description TEXT

-- Indexes for performance
CREATE INDEX idx_estimates_media_group_id ON estimates(media_group_id);
CREATE INDEX idx_estimates_created_at ON estimates(created_at DESC);
```

**Purpose**:
- `photo_ids`: Support multiple photos in a single estimate
- `media_group_id`: Link estimates to Telegram media groups
- `description`: Store user-provided descriptions
- Indexes: Improve estimate lookup and media group queries

## New Tables

### 1. Daily Summary Table

```sql
CREATE TABLE daily_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_date DATE NOT NULL,
    meal_count INTEGER NOT NULL DEFAULT 0,
    total_calories DECIMAL(8,2) NOT NULL DEFAULT 0,
    total_protein DECIMAL(8,2) NOT NULL DEFAULT 0,
    total_carbs DECIMAL(8,2) NOT NULL DEFAULT 0,
    total_fats DECIMAL(8,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure one summary per user per day
    UNIQUE(user_id, meal_date)
);

-- Indexes for performance
CREATE INDEX idx_daily_summary_user_date ON daily_summary(user_id, meal_date DESC);
CREATE INDEX idx_daily_summary_date ON daily_summary(meal_date DESC);
```

**Purpose**:
- Pre-computed daily meal summaries for calendar views
- Efficient aggregation of meal data by date
- Supports fast calendar queries without real-time aggregation

## Migration Scripts

### Migration 1: Add Photo Display Order

```sql
-- Add display_order column to photos table
ALTER TABLE photos ADD COLUMN display_order INTEGER NOT NULL DEFAULT 0;

-- Add constraint for display order range
ALTER TABLE photos ADD CONSTRAINT check_display_order
    CHECK (display_order >= 0 AND display_order <= 4);

-- Add index for efficient ordering
CREATE INDEX idx_photos_meal_display_order ON photos(meal_id, display_order);
```

### Migration 2: Add Media Group Support

```sql
-- Add media_group_id to photos table
ALTER TABLE photos ADD COLUMN media_group_id TEXT;

-- Add media_group_id to estimates table
ALTER TABLE estimates ADD COLUMN media_group_id TEXT;

-- Add indexes for media group queries
CREATE INDEX idx_photos_media_group_id ON photos(media_group_id);
CREATE INDEX idx_estimates_media_group_id ON estimates(media_group_id);
```

### Migration 3: Enhance Meals Table

```sql
-- Extend description field
ALTER TABLE meals ALTER COLUMN description TYPE TEXT;

-- Add confidence score
ALTER TABLE meals ADD COLUMN confidence_score DECIMAL(3,2);

-- Add constraint for confidence score
ALTER TABLE meals ADD CONSTRAINT check_confidence_score
    CHECK (confidence_score >= 0 AND confidence_score <= 1);

-- Add performance indexes
CREATE INDEX idx_meals_user_created ON meals(user_id, created_at DESC);
CREATE INDEX idx_meals_created_at ON meals(created_at DESC);
```

### Migration 4: Create Daily Summary Table

```sql
-- Create daily_summary table
CREATE TABLE daily_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_date DATE NOT NULL,
    meal_count INTEGER NOT NULL DEFAULT 0,
    total_calories DECIMAL(8,2) NOT NULL DEFAULT 0,
    total_protein DECIMAL(8,2) NOT NULL DEFAULT 0,
    total_carbs DECIMAL(8,2) NOT NULL DEFAULT 0,
    total_fats DECIMAL(8,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, meal_date)
);

-- Add indexes
CREATE INDEX idx_daily_summary_user_date ON daily_summary(user_id, meal_date DESC);
CREATE INDEX idx_daily_summary_date ON daily_summary(meal_date DESC);
```

## Data Integrity Constraints

### Photo Constraints
- Maximum 5 photos per meal (enforced by `display_order` constraint)
- Unique `display_order` per meal (enforced by application logic)
- Valid `display_order` range (0-4)

### Meal Constraints
- Valid `confidence_score` range (0-1)
- Non-negative macronutrient values
- Valid date ranges for calendar queries

### Daily Summary Constraints
- One summary per user per day (enforced by unique constraint)
- Non-negative aggregate values
- Automatic updates via triggers or application logic

## Performance Optimizations

### Indexes Added
1. **Photos Table**:
   - `idx_photos_meal_id`: Fast meal photo retrieval
   - `idx_photos_media_group_id`: Media group queries
   - `idx_photos_meal_display_order`: Ordered photo display

2. **Meals Table**:
   - `idx_meals_user_created`: User meal history queries
   - `idx_meals_created_at`: General meal queries

3. **Daily Summary Table**:
   - `idx_daily_summary_user_date`: Calendar queries
   - `idx_daily_summary_date`: Date-based queries

### Query Optimizations
- Pre-computed daily summaries for calendar views
- Efficient photo ordering with display_order
- Optimized meal history queries with proper indexing

## Backward Compatibility

### Existing Data
- All existing photos get `display_order = 0`
- Existing meals remain unchanged
- No data loss during migration

### API Compatibility
- Existing API endpoints continue to work
- New fields are optional in responses
- Graceful handling of missing new fields

## Rollback Plan

### Rollback Steps
1. Drop new indexes
2. Remove new columns
3. Drop new tables
4. Restore original constraints

### Rollback Scripts
```sql
-- Rollback Migration 4
DROP TABLE IF EXISTS daily_summary;

-- Rollback Migration 3
ALTER TABLE meals DROP COLUMN IF EXISTS confidence_score;
ALTER TABLE meals ALTER COLUMN description TYPE VARCHAR(255);
DROP INDEX IF EXISTS idx_meals_user_created;
DROP INDEX IF EXISTS idx_meals_created_at;

-- Rollback Migration 2
ALTER TABLE photos DROP COLUMN IF EXISTS media_group_id;
ALTER TABLE estimates DROP COLUMN IF EXISTS media_group_id;
DROP INDEX IF EXISTS idx_photos_media_group_id;
DROP INDEX IF EXISTS idx_estimates_media_group_id;

-- Rollback Migration 1
ALTER TABLE photos DROP COLUMN IF EXISTS display_order;
DROP INDEX IF EXISTS idx_photos_meal_display_order;
```

## Monitoring and Maintenance

### Performance Monitoring
- Monitor query performance for new indexes
- Track daily summary table growth
- Monitor photo storage usage

### Maintenance Tasks
- Regular index maintenance
- Daily summary table cleanup (old data)
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
