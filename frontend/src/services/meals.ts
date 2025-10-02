/**
 * Meals Service
 * Feature: 003-update-logic-for
 * Task: T054
 *
 * API client for meal management operations
 */

import { api } from './api';

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

export interface MealsListResponse {
  meals: Meal[];
  total: number;
}

export interface CalendarDay {
  meal_date: string;
  meal_count: number;
  total_calories: number;
  total_protein: number;
  total_carbs: number;
  total_fats: number;
}

export interface MealsCalendarResponse {
  dates: CalendarDay[];
}

/**
 * Get meals for a specific date or date range
 * Feature: 003-update-logic-for
 */
export async function getMeals(date?: string, startDate?: string, endDate?: string, limit: number = 50): Promise<MealsListResponse> {
  const params = new URLSearchParams();

  if (date) {
    params.append('date', date);
  } else if (startDate && endDate) {
    params.append('start_date', startDate);
    params.append('end_date', endDate);
  }

  if (limit) {
    params.append('limit', limit.toString());
  }

  const url = `/api/v1/meals${params.toString() ? `?${params.toString()}` : ''}`;
  const response = await api.get<MealsListResponse>(url);
  return response.data;
}

/**
 * Get a specific meal by ID
 * Feature: 003-update-logic-for
 */
export async function getMeal(mealId: string): Promise<Meal> {
  const response = await api.get<Meal>(`/api/v1/meals/${mealId}`);
  return response.data;
}

/**
 * Update meal details
 * Feature: 003-update-logic-for
 */
export async function updateMeal(mealId: string, updates: MealUpdate): Promise<Meal> {
  const response = await api.patch<Meal>(`/api/v1/meals/${mealId}`, updates);
  return response.data;
}

/**
 * Delete a meal
 * Feature: 003-update-logic-for
 */
export async function deleteMeal(mealId: string): Promise<void> {
  await api.delete(`/api/v1/meals/${mealId}`);
}

/**
 * Get calendar summary for date range
 * Feature: 003-update-logic-for
 */
export async function getMealsCalendar(startDate: string, endDate: string): Promise<MealsCalendarResponse> {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
  });

  const response = await api.get<MealsCalendarResponse>(`/api/v1/meals/calendar?${params.toString()}`);
  return response.data;
}

export default {
  getMeals,
  getMeal,
  updateMeal,
  deleteMeal,
  getMealsCalendar,
};
