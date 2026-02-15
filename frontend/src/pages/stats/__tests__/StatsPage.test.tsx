import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { handlers } from '@/test/handlers';
import { renderWithProviders } from '@/test/utils';
import StatsPage from '../index';

const API_BASE = 'http://localhost:8000';

const statsHandlers = [
  ...handlers,
  http.get(`${API_BASE}/api/v1/statistics/daily`, () =>
    HttpResponse.json({
      data: [{ date: '2026-02-15', total_calories: 1800, total_protein: 120, total_fat: 60, total_carbs: 200, meal_count: 3, goal_calories: 2000, goal_achievement: 0.9 }],
      period: { start_date: '2026-02-09', end_date: '2026-02-15', total_days: 7 },
      summary: { total_meals: 3, average_daily_calories: 1800, average_goal_achievement: 0.9 },
    }),
  ),
  http.get(`${API_BASE}/api/v1/statistics/macros`, () =>
    HttpResponse.json({
      protein_percent: 30, fat_percent: 25, carbs_percent: 45,
      protein_grams: 120, fat_grams: 60, carbs_grams: 200, total_calories: 1800,
      period: { start_date: '2026-02-09', end_date: '2026-02-15', total_days: 7 },
    }),
  ),
];

const server = setupServer(...statsHandlers);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('StatsPage', () => {
  it('renders stats title', () => {
    renderWithProviders(<StatsPage />);
    expect(screen.getByText(/.*(stat|nutrition)/i)).toBeInTheDocument();
  });

  it('renders period selector', () => {
    renderWithProviders(<StatsPage />);
    expect(screen.getByText(/7/)).toBeInTheDocument();
    expect(screen.getByText(/30/)).toBeInTheDocument();
  });
});
