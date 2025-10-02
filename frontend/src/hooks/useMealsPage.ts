/**
 * useMealsPage Hook
 * Feature: 003-update-logic-for
 * Task: T053
 *
 * Optimized React hook for meals page data fetching
 * - Fetches meals, calendar, and goals in parallel
 * - Reduces API requests and improves performance
 */

import { useState, useEffect, useCallback } from 'react';
import { getMeals, getMealsCalendar, updateMeal, deleteMeal, type Meal, type MealUpdate, type CalendarDay } from '../services/meals';
import { goalsApi, type Goal } from '../services/api';

// Re-export types for convenience
export type { Meal, MealUpdate, CalendarDay, Goal };

export interface MealsPageData {
  meals: Meal[];
  calendarData: CalendarDay[];
  goal: Goal | null;
  loading: boolean;
  error: string | null;
}

export function useMealsPage(selectedDate: Date) {
  const [data, setData] = useState<MealsPageData>({
    meals: [],
    calendarData: [],
    goal: null,
    loading: false,
    error: null,
  });

  const fetchData = useCallback(async (date: Date) => {
    setData(prev => ({ ...prev, loading: true, error: null }));

    try {
      const dateStr = date.toISOString().split('T')[0];

      // Calculate calendar dates
      const endDate = new Date();
      const startDate = new Date();
      startDate.setMonth(startDate.getMonth() - 1);
      const startDateStr = startDate.toISOString().split('T')[0];
      const endDateStr = endDate.toISOString().split('T')[0];

      // Fetch all data in parallel
      const [mealsResult, calendarResult, goalResult] = await Promise.allSettled([
        getMeals(dateStr),
        getMealsCalendar(startDateStr, endDateStr),
        goalsApi.getGoal(),
      ]);

      // Process results
      const meals = mealsResult.status === 'fulfilled' ? mealsResult.value.meals : [];
      const calendarData = calendarResult.status === 'fulfilled' ? calendarResult.value.dates : [];
      const goal = goalResult.status === 'fulfilled' ? goalResult.value : null;

      setData({
        meals,
        calendarData,
        goal,
        loading: false,
        error: null,
      });
    } catch (err) {
      setData(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : 'Failed to fetch data',
      }));
      console.error('Error fetching meals page data:', err);
    }
  }, []);

  // Fetch data when selected date changes
  useEffect(() => {
    fetchData(selectedDate);
  }, [selectedDate, fetchData]);

  // Update meal with optimistic update
  const handleUpdateMeal = useCallback(async (mealId: string, updates: MealUpdate) => {
    const originalMeals = [...data.meals];

    try {
      // Optimistic update
      setData(prev => ({
        ...prev,
        meals: prev.meals.map(meal => {
          if (meal.id === mealId) {
            // Calculate new calories if macros changed
            const protein = updates.protein_grams ?? meal.macronutrients.protein;
            const carbs = updates.carbs_grams ?? meal.macronutrients.carbs;
            const fats = updates.fats_grams ?? meal.macronutrients.fats;
            const newCalories = protein * 4 + carbs * 4 + fats * 9;

            return {
              ...meal,
              description: updates.description ?? meal.description,
              macronutrients: {
                protein,
                carbs,
                fats,
              },
              calories: newCalories,
            };
          }
          return meal;
        }),
      }));

      // Actual API call
      const updatedMeal = await updateMeal(mealId, updates);

      // Replace with server response
      setData(prev => ({
        ...prev,
        meals: prev.meals.map(meal => meal.id === mealId ? updatedMeal : meal),
      }));
    } catch (err) {
      // Revert on error
      setData(prev => ({ ...prev, meals: originalMeals }));
      throw err;
    }
  }, [data.meals]);

  // Delete meal with optimistic update
  const handleDeleteMeal = useCallback(async (mealId: string) => {
    const originalMeals = [...data.meals];

    try {
      // Optimistic delete
      setData(prev => ({
        ...prev,
        meals: prev.meals.filter(meal => meal.id !== mealId),
      }));

      // Actual API call
      await deleteMeal(mealId);
    } catch (err) {
      // Revert on error
      setData(prev => ({ ...prev, meals: originalMeals }));
      throw err;
    }
  }, [data.meals]);

  return {
    meals: data.meals,
    calendarData: data.calendarData,
    goal: data.goal,
    loading: data.loading,
    error: data.error,
    refetch: fetchData,
    updateMeal: handleUpdateMeal,
    deleteMeal: handleDeleteMeal,
  };
}

export default useMealsPage;
