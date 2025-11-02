-- Add statistics support for meals table
-- Feature: 005-mini-app-improvements

-- Create index for statistics queries
CREATE INDEX IF NOT EXISTS idx_meals_user_created ON public.meals(user_id, created_at);

-- Create function for daily statistics aggregation
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

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION public.query_daily_statistics(UUID, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.query_daily_statistics(UUID, TEXT, TEXT) TO anon;
