# Data Model (Phase 1) — Frontend View Models

This document enumerates UI-facing view models, core fields, and relationships derived from the feature specification.

## Entities

### User
- id: string (UUID)
- telegram_user_id: integer (Telegram account id)
- language: enum [en, ru]
- created_at: datetime
- updated_at: datetime

### FoodPhoto
- id: string (UUID)
- user_id: string (FK → User.id)
- object_key: string (S3/Tigris key)
- content_type: string (MIME)
- created_at: datetime

### Estimate
- id: string (UUID)
- photo_id: string (FK → FoodPhoto.id)
- kcal_mean: number
- kcal_min: number
- kcal_max: number
- confidence: number (0..1)
- breakdown: array of { label: string, kcal: number, confidence: number }
- status: enum [queued, running, done, failed]
- created_at: datetime
- updated_at: datetime

### Meal
- id: string (UUID)
- user_id: string (FK → User.id)
- meal_date: date
- meal_type: enum [breakfast, lunch, dinner, snack]
- kcal_total: number
- macros: object { protein_g?: number, fat_g?: number, carbs_g?: number }
- estimate_id: string (nullable, FK → Estimate.id)
- corrected: boolean (true if user adjusted values)
- created_at: datetime
- updated_at: datetime

### DailySummary (derived)
- user_id: string
- date: date
- kcal_total: number
- macros_totals: object { protein_g?: number, fat_g?: number, carbs_g?: number }

### Goal
- user_id: string (FK → User.id)
- daily_kcal_target: number
- created_at: datetime
- updated_at: datetime

## Relationships
- User 1—* FoodPhoto
- FoodPhoto 1—1..* Estimate (latest used for Meal when status=done)
- User 1—* Meal (optionally referencing Estimate)
- User 1—1 Goal (latest active)

## Validation Rules
- Meal.meal_date must be a valid date; cannot be far in the future.
- Meal requires either kcal_total/macros or reference to a completed Estimate (overrides allowed in UI).
- Estimate.status must be `done` before linking to a Meal.
- FoodPhoto.content_type must be an allowed image MIME type.
- User.language ∈ {en, ru}.
