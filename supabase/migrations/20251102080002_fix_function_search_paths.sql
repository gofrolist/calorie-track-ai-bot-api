-- Fix search_path security warnings for functions
-- Feature: 005-mini-app-improvements
-- This migration updates existing functions to fix security warnings

-- Fix query_daily_statistics function with explicit search_path
CREATE OR REPLACE FUNCTION public.query_daily_statistics(
    p_user_id UUID,
    p_start_date TEXT,
    p_end_date TEXT
)
RETURNS TABLE (
    meal_date DATE,
    total_calories NUMERIC,
    total_protein NUMERIC,
    total_fat NUMERIC,
    total_carbs NUMERIC,
    meal_count BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.meal_date,
        COALESCE(SUM(m.kcal_total), 0) as total_calories,
        COALESCE(SUM(m.protein_grams), 0) as total_protein,
        COALESCE(SUM(m.fats_grams), 0) as total_fat,
        COALESCE(SUM(m.carbs_grams), 0) as total_carbs,
        COUNT(*)::BIGINT as meal_count
    FROM public.meals m
    WHERE
        m.user_id = p_user_id
        AND m.created_at >= p_start_date::timestamp with time zone
        AND m.created_at < p_end_date::timestamp with time zone
    GROUP BY m.meal_date
    ORDER BY m.meal_date ASC;
END;
$$;

-- Fix update_updated_at_column function with explicit search_path
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;
