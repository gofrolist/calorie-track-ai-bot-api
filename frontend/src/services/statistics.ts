/**
 * Statistics API Client Service
 * Feature: 005-mini-app-improvements
 *
 * Handles retrieval of nutrition statistics for data visualization
 */

import { api } from './api';

/**
 * Single day's aggregated nutrition data
 */
export interface DailyDataPoint {
  date: string;  // YYYY-MM-DD format
  total_calories: number;
  total_protein: number;
  total_fat: number;
  total_carbs: number;
  meal_count: number;
  goal_calories?: number | null;
  goal_achievement?: number | null;
}

/**
 * Time period for statistics
 */
export interface StatisticsPeriod {
  start_date: string;
  end_date: string;
  total_days: number;
}

/**
 * Summary statistics for period
 */
export interface StatisticsSummary {
  total_meals: number;
  average_daily_calories: number;
  average_goal_achievement?: number | null;
}

/**
 * Daily statistics response
 */
export interface DailyStatisticsResponse {
  data: DailyDataPoint[];
  period: StatisticsPeriod;
  summary: StatisticsSummary;
}

/**
 * Macronutrient breakdown response
 */
export interface MacroStatisticsResponse {
  protein_percent: number;
  fat_percent: number;
  carbs_percent: number;
  protein_grams: number;
  fat_grams: number;
  carbs_grams: number;
  total_calories: number;
  period: StatisticsPeriod;
}

/**
 * Date range preset options
 */
export type DateRangePreset = '7days' | '30days' | '90days' | 'custom';

/**
 * Get daily nutrition statistics
 *
 * @param startDate - Start date (inclusive)
 * @param endDate - End date (exclusive)
 * @returns Daily statistics with data points and summary
 * @throws Error if query fails
 */
export async function getDailyStatistics(
  startDate: string,
  endDate: string
): Promise<DailyStatisticsResponse> {
  const response = await api.get<DailyStatisticsResponse>(
    '/api/v1/statistics/daily',
    {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    }
  );
  return response.data;
}

/**
 * Get macronutrient breakdown statistics
 *
 * @param startDate - Start date (inclusive)
 * @param endDate - End date (exclusive)
 * @returns Macro breakdown with percentages and grams
 * @throws Error if query fails
 */
export async function getMacroStatistics(
  startDate: string,
  endDate: string
): Promise<MacroStatisticsResponse> {
  const response = await api.get<MacroStatisticsResponse>(
    '/api/v1/statistics/macros',
    {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    }
  );
  return response.data;
}

/**
 * Calculate date range for preset
 *
 * @param preset - Date range preset (7days, 30days, 90days)
 * @returns Object with start_date and end_date strings
 */
export function calculateDateRange(preset: DateRangePreset): { start_date: string; end_date: string } {
  const today = new Date();
  const endDate = new Date(today);
  endDate.setDate(endDate.getDate() + 1); // End date exclusive (tomorrow)

  const startDate = new Date(today);

  switch (preset) {
    case '7days':
      startDate.setDate(startDate.getDate() - 6); // Last 7 days including today
      break;
    case '30days':
      startDate.setDate(startDate.getDate() - 29); // Last 30 days including today
      break;
    case '90days':
      startDate.setDate(startDate.getDate() - 89); // Last 90 days including today
      break;
    case 'custom':
      // Custom range handled by caller
      break;
  }

  return {
    start_date: startDate.toISOString().split('T')[0],
    end_date: endDate.toISOString().split('T')[0],
  };
}

/**
 * Format date for display
 *
 * @param dateString - Date string in YYYY-MM-DD format
 * @param locale - Locale for formatting (en, ru)
 * @returns Formatted date string
 */
export function formatDateForDisplay(dateString: string, locale: string = 'en'): string {
  const date = new Date(dateString);
  return date.toLocaleDateString(locale, {
    month: 'short',
    day: 'numeric',
  });
}
