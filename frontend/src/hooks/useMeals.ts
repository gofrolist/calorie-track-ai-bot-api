/**
 * useMeals Hook
 * Feature: 003-update-logic-for
 * Task: T053
 *
 * React hook for meal data fetching and management
 * - Fetches meals by date
 * - Supports calendar date range queries
 * - Handles meal CRUD operations
 * - Optimistic updates
 */

import { useState, useEffect, useCallback } from 'react';
import { getMeals, updateMeal, deleteMeal, getMealsCalendar } from '../services/meals';

export interface Macronutrients {
  protein: number;
  carbs: number;
  fats: number;
}

export interface Photo {
  id: string;
  thumbnailUrl: string;
  fullUrl: string;
  displayOrder: number;
}

export interface Meal {
  id: string;
  userId: string;
  createdAt: string;
  description: string | null;
  calories: number;
  macronutrients: Macronutrients;
  photos: Photo[];
  confidenceScore: number | null;
}

export interface MealUpdate {
  description?: string;
  protein_grams?: number;
  carbs_grams?: number;
  fats_grams?: number;
}

export interface CalendarDay {
  meal_date: string;
  meal_count: number;
  total_calories: number;
  total_protein: number;
  total_carbs: number;
  total_fats: number;
}

export function useMeals(selectedDate?: Date) {
  const [meals, setMeals] = useState<Meal[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMeals = useCallback(async (date?: Date) => {
    setLoading(true);
    setError(null);

    try {
      const dateStr = date ? date.toISOString().split('T')[0] : undefined;
      const response = await getMeals(dateStr);
      setMeals(response.meals);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch meals');
      console.error('Error fetching meals:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch meals when selected date changes
  useEffect(() => {
    fetchMeals(selectedDate);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate]);

  // Update meal with optimistic update
  const handleUpdateMeal = useCallback(async (mealId: string, updates: MealUpdate) => {
    const originalMeals = [...meals];

    try {
      // Optimistic update
      setMeals(prevMeals =>
        prevMeals.map(meal => {
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
        })
      );

      // Actual API call
      const updatedMeal = await updateMeal(mealId, updates);

      // Replace with server response
      setMeals(prevMeals =>
        prevMeals.map(meal => meal.id === mealId ? updatedMeal : meal)
      );
    } catch (err) {
      // Revert on error
      setMeals(originalMeals);
      setError(err instanceof Error ? err.message : 'Failed to update meal');
      throw err;
    }
  }, [meals]);

  // Delete meal with optimistic update
  const handleDeleteMeal = useCallback(async (mealId: string) => {
    const originalMeals = [...meals];

    try {
      // Optimistic delete
      setMeals(prevMeals => prevMeals.filter(meal => meal.id !== mealId));

      // Actual API call
      await deleteMeal(mealId);
    } catch (err) {
      // Revert on error
      setMeals(originalMeals);
      setError(err instanceof Error ? err.message : 'Failed to delete meal');
      throw err;
    }
  }, [meals]);

  return {
    meals,
    loading,
    error,
    refetch: fetchMeals,
    updateMeal: handleUpdateMeal,
    deleteMeal: handleDeleteMeal,
  };
}

export function useMealsCalendar(startDate: Date, endDate: Date) {
  const [calendarData, setCalendarData] = useState<CalendarDay[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCalendar = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const startStr = startDate.toISOString().split('T')[0];
      const endStr = endDate.toISOString().split('T')[0];

      const response = await getMealsCalendar(startStr, endStr);
      setCalendarData(response.dates);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch calendar data');
      console.error('Error fetching calendar:', err);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => {
    fetchCalendar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDate, endDate]);

  return {
    calendarData,
    loading,
    error,
    refetch: fetchCalendar,
  };
}

export default useMeals;
