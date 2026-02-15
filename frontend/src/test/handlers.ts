import { http, HttpResponse } from 'msw';

const API_BASE = 'http://localhost:8000';

export const handlers = [
  http.get(`${API_BASE}/health/live`, () =>
    HttpResponse.json({ status: 'ok' }),
  ),
  http.get(`${API_BASE}/api/v1/goals`, () =>
    HttpResponse.json({ id: '1', user_id: '123', daily_kcal_target: 2000, created_at: '2026-01-01', updated_at: '2026-01-01' }),
  ),
  http.get(`${API_BASE}/api/v1/meals`, () =>
    HttpResponse.json({ meals: [], total: 0 }),
  ),
  http.get(`${API_BASE}/api/v1/daily-summary/:date`, () =>
    HttpResponse.json({ user_id: '123', date: '2026-02-15', kcal_total: 0, macros_totals: { protein_g: 0, fat_g: 0, carbs_g: 0 } }),
  ),
  http.get(`${API_BASE}/api/v1/meals/calendar`, () =>
    HttpResponse.json({ dates: [] }),
  ),
];
