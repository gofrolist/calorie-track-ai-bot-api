# Data Model: Multi-Photo Meal Tracking & Enhanced Meals History

**Feature**: 003-update-logic-for
**Date**: 2025-09-30

## Overview

This data model extends the existing schema to support multi-photo meals, macronutrient storage, and enhanced meal history. Changes are backward-compatible and build upon current database structure.

## Entity Relationship Diagram

```
User (existing)
  │
  ├──< Meal (extended)
  │     ├── protein_grams (NEW)
  │     ├── carbs_grams (NEW)
  │     ├── fats_grams (NEW)
  │     ├── description (extended - now optional with photos)
  │     │
  │     └──< Photo (extended)
  │           ├── meal_id (NEW - foreign key)
  │           ├── media_group_id (NEW - Telegram grouping)
  │           ├── display_order (NEW - carousel sequence)
  │           └── estimate_id (existing - kept for backward compat)
  │
  └──< DailySummary (existing, to be extended)
        ├── total_protein_grams (NEW)
        ├── total_carbs_grams (NEW)
        ├── total_fats_grams (NEW)
```

## Core Entities

### 1. Meal (Extended)

**Purpose**: Represents a single food intake event, potentially with multiple photos

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, NOT NULL | Unique meal identifier |
| user_id | UUID | FK → users.id, NOT NULL | Owner of the meal |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Meal creation time |
| description | TEXT | NULLABLE | User-provided description (optional) |
| calories | DECIMAL(7,2) | NOT NULL | Total calories estimate |
| protein_grams | DECIMAL(6,2) | **NEW**, NULLABLE | Protein content in grams |
| carbs_grams | DECIMAL(6,2) | **NEW**, NULLABLE | Carbohydrate content in grams |
| fats_grams | DECIMAL(6,2) | **NEW**, NULLABLE | Fat content in grams |
| confidence_score | DECIMAL(3,2) | NULLABLE | AI estimation confidence (0-1) |
| estimate_id | UUID | FK → estimates.id, NULLABLE | Legacy: estimation record |

**Indexes**:
- `idx_meals_user_created` ON (user_id, created_at DESC) - for history queries
- `idx_meals_created_at` ON (created_at) - for retention filtering

**Validation Rules**:
- `created_at` must be within last 1 year for display
- `calories` must be >= 0
- `protein_grams`, `carbs_grams`, `fats_grams` must be >= 0 if set
- User must own meal for any updates/deletes
- At least one of (description, photos) must be present

**State Transitions**:
- Created → Active (normal state)
- Active → Updated (when edited)
- Active → Deleted (soft/hard delete TBD)

### 2. Photo (Extended)

**Purpose**: Represents a meal photo with Telegram context and meal association

**Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, NOT NULL | Unique photo identifier |
| user_id | UUID | FK → users.id, NOT NULL | Owner of the photo |
| file_key | VARCHAR(500) | NOT NULL, UNIQUE | S3/Tigris storage key |
| uploaded_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Upload timestamp |
| meal_id | UUID | **NEW**, FK → meals.id, NULLABLE | Associated meal (NULL if pre-estimation) |
| estimate_id | UUID | FK → estimates.id, NULLABLE | Legacy: estimation record |
| media_group_id | VARCHAR(255) | **NEW**, NULLABLE | Telegram media group ID |
| display_order | INTEGER | **NEW**, DEFAULT 0 | Position in carousel (0-indexed) |
| file_size | INTEGER | NULLABLE | File size in bytes |
| mime_type | VARCHAR(50) | NULLABLE | Image MIME type |

**Indexes**:
- `idx_photos_meal_id` ON (meal_id) - for fetching meal photos
- `idx_photos_media_group` ON (media_group_id) - for Telegram grouping
- `idx_photos_user_uploaded` ON (user_id, uploaded_at DESC) - for user photo history

**Validation Rules**:
- `display_order` must be 0-4 (max 5 photos)
- `file_size` must not exceed 20MB (Telegram limit)
- `mime_type` must be image/* format
- Photos with same `media_group_id` must have same `meal_id`

**Cascade Behaviors**:
- ON DELETE meal → CASCADE (delete photos when meal deleted)
- ON DELETE estimate → SET NULL (preserve photo if estimate deleted)

### 3. Estimate (Existing, Minor Extension)

**Purpose**: Stores AI estimation results

**Extended Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| ... | ... | ... | (existing fields unchanged) |
| macronutrients | JSONB | **NEW**, NULLABLE | Detailed macro breakdown: {"protein": 25.5, "carbs": 50.0, "fats": 15.0} |
| photo_count | INTEGER | **NEW**, DEFAULT 1 | Number of photos analyzed |

**Notes**:
- Backward compatible - existing single-photo estimates work unchanged
- `macronutrients` JSONB allows flexibility for future nutrients
- `photo_count` enables analytics on multi-photo usage

### 4. DailySummary (Existing, Extension Required)

**Purpose**: Aggregated daily nutrition data

**Extended Fields**:

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| ... | ... | ... | (existing fields) |
| total_protein_grams | DECIMAL(8,2) | **NEW**, DEFAULT 0 | Daily total protein |
| total_carbs_grams | DECIMAL(8,2) | **NEW**, DEFAULT 0 | Daily total carbs |
| total_fats_grams | DECIMAL(8,2) | **NEW**, DEFAULT 0 | Daily total fats |

**Update Triggers**:
- Recalculate when meal created/updated/deleted
- Atomic update with meal operation (transaction)

## Supporting Structures

### MealWithPhotos (View/DTO)

**Purpose**: Convenient query structure for frontend

```typescript
interface MealWithPhotos {
  id: string;
  userId: string;
  createdAt: Date;
  description: string | null;
  calories: number;
  macronutrients: {
    protein: number;
    carbs: number;
    fats: number;
  };
  photos: Array<{
    id: string;
    fileKey: string;
    thumbnailUrl: string;
    fullUrl: string;
    displayOrder: number;
  }>;
  confidenceScore: number | null;
}
```

### MealUpdate (DTO)

**Purpose**: Update meal via PATCH endpoint

```typescript
interface MealUpdate {
  description?: string;
  protein_grams?: number;
  carbs_grams?: number;
  fats_grams?: number;
  // calories auto-recalculated from macros if changed
}
```

## Database Migration Plan

### Migration: `[timestamp]_multiphotos_meals.sql`

```sql
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
```

## Query Patterns

### Fetch Meals for Date with Photos

```sql
SELECT
  m.*,
  COALESCE(
    json_agg(
      json_build_object(
        'id', p.id,
        'fileKey', p.file_key,
        'displayOrder', p.display_order
      ) ORDER BY p.display_order
    ) FILTER (WHERE p.id IS NOT NULL),
    '[]'
  ) as photos
FROM meals m
LEFT JOIN photos p ON p.meal_id = m.id
WHERE m.user_id = $1
  AND DATE(m.created_at) = $2
  AND m.created_at >= NOW() - INTERVAL '1 year'
GROUP BY m.id
ORDER BY m.created_at DESC;
```

### Get Meals with Macronutrients for Calendar Range

```sql
SELECT
  DATE(created_at) as date,
  COUNT(*) as meal_count,
  SUM(protein_grams) as total_protein,
  SUM(carbs_grams) as total_carbs,
  SUM(fats_grams) as total_fats
FROM meals
WHERE user_id = $1
  AND created_at >= $2 AND created_at < $3
  AND created_at >= NOW() - INTERVAL '1 year'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Update Meal and Recalculate Calories

```sql
-- Calorie calculation: 4 kcal/g protein, 4 kcal/g carbs, 9 kcal/g fats
UPDATE meals
SET
  description = COALESCE($2, description),
  protein_grams = COALESCE($3, protein_grams),
  carbs_grams = COALESCE($4, carbs_grams),
  fats_grams = COALESCE($5, fats_grams),
  calories = (
    COALESCE($3, protein_grams, 0) * 4 +
    COALESCE($4, carbs_grams, 0) * 4 +
    COALESCE($5, fats_grams, 0) * 9
  )
WHERE id = $1 AND user_id = $6
RETURNING *;
```

## Data Retention

**Policy**: 1 year from meal creation

**Implementation**:
- Filter queries: `WHERE created_at >= NOW() - INTERVAL '1 year'`
- Optional archival job (monthly): Move/delete meals older than 365 days
- Include photos in archival (delete from Tigris storage)
- Cascade deletes handle photo cleanup automatically

**GDPR Considerations**:
- User export includes all meals with macronutrients
- User deletion cascades to meals → photos
- Retention period documented in privacy policy

## Validation Summary

| Entity | Validation Rules |
|--------|-----------------|
| Meal | - created_at within 1 year<br>- calories >= 0<br>- macros >= 0 if set<br>- user owns meal<br>- has description OR photos |
| Photo | - display_order 0-4<br>- file_size <= 20MB<br>- valid image mime_type<br>- media_group_id consistency<br>- user owns photo |
| Estimate | - photo_count >= 1<br>- macronutrients valid if set |
| DailySummary | - totals >= 0<br>- recalculated atomically |

## Performance Considerations

- **Indexes**: Optimize for date-range queries and meal-photo JOINs
- **Aggregation**: Use json_agg for efficient photo fetching
- **Caching**: Consider Redis cache for frequently accessed date ranges
- **Pagination**: Limit query results, use cursor-based pagination for large histories
- **Image URLs**: Generate presigned URLs lazily, cache for 1 hour

---

*This data model is backward compatible with existing schema and supports all feature requirements from spec.md*
