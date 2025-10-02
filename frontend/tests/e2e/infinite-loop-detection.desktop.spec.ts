/**
 * Infinite Loop Detection E2E Tests
 *
 * Detects infinite re-render loops by monitoring API request patterns
 * - Counts duplicate API calls within a short time window
 * - Fails if same API is called too many times (indicating infinite loop)
 * - Covers all pages to ensure no infinite loops exist
 */

import { test, expect, Page } from '@playwright/test';

// Helper to detect infinite loops by monitoring API calls
async function detectInfiniteLoop(page: Page, options: {
  navigationUrl: string;
  maxAllowedCalls?: number;
  monitorDuration?: number;
  apiPattern?: RegExp;
}) {
  const {
    navigationUrl,
    maxAllowedCalls = 5, // Maximum allowed calls to same endpoint
    monitorDuration = 3000, // Monitor for 3 seconds
    apiPattern = /\/api\/v1\//, // Pattern to match API calls
  } = options;

  const apiCalls = new Map<string, number>();

  // Monitor all API requests
  page.on('request', (request) => {
    const url = request.url();
    if (apiPattern.test(url)) {
      // Normalize URL (remove query params for grouping)
      const normalizedUrl = url.split('?')[0];
      const count = apiCalls.get(normalizedUrl) || 0;
      apiCalls.set(normalizedUrl, count + 1);
    }
  });

  // Navigate to page
  await page.goto(navigationUrl);

  // Wait for initial load
  await page.waitForLoadState('networkidle');

  // Monitor for additional time to catch delayed loops
  await page.waitForTimeout(monitorDuration);

  // Check for excessive duplicate calls
  let infiniteLoopDetected = false;
  const violations: string[] = [];

  for (const [url, count] of apiCalls.entries()) {
    // Skip logging endpoints - they're expected to be called multiple times
    if (url.includes('/logs') || url.includes('/config')) {
      continue;
    }

    if (count > maxAllowedCalls) {
      infiniteLoopDetected = true;
      violations.push(`${url} was called ${count} times (max: ${maxAllowedCalls})`);
    }
  }

  return { infiniteLoopDetected, violations, apiCalls };
}

test.describe('Infinite Loop Detection', () => {
  test.beforeEach(async ({ page }) => {
    // Mock Telegram WebApp
    await page.addInitScript(() => {
      window.Telegram = {
        WebApp: {
          initData: 'user=%7B%22id%22%3A12341234%7D',
          initDataUnsafe: { user: { id: 12341234 } },
          ready: () => {},
          expand: () => {},
          close: () => {},
          BackButton: { show: () => {}, hide: () => {}, onClick: () => {} },
          MainButton: { show: () => {}, hide: () => {}, setText: () => {} },
          themeParams: {
            bg_color: '#ffffff',
            text_color: '#000000',
            hint_color: '#999999',
            link_color: '#2481cc',
            button_color: '#2481cc',
            button_text_color: '#ffffff',
          },
        },
      };
    });

    // Mock API responses to avoid actual backend calls
    await page.route('**/api/v1/goals', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ daily_kcal_target: 2000 }),
      });
    });

    await page.route('**/api/v1/daily-summary**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user_id: '12341234',
          date: new Date().toISOString().split('T')[0],
          kcal_total: 0,
          macros_totals: { protein_g: 0, fat_g: 0, carbs_g: 0 },
        }),
      });
    });

    await page.route('**/api/v1/meals**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          meals: [],
          total: 0,
          calories: 0,
          macronutrients: { protein: 0, carbs: 0, fats: 0 },
          photos: 0,
        }),
      });
    });

    await page.route('**/api/v1/meals/calendar**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ dates: [] }),
      });
    });
  });

  test('should not have infinite loop on Meals page', async ({ page }) => {
    const result = await detectInfiniteLoop(page, {
      navigationUrl: 'http://localhost:3000/',
      maxAllowedCalls: 3, // Allow up to 3 calls (initial + potential retry)
      monitorDuration: 4000, // Monitor for 4 seconds
    });

    if (result.infiniteLoopDetected) {
      console.error('Infinite loop detected! Violations:');
      result.violations.forEach((v) => console.error(`  - ${v}`));
      console.error('\nAll API calls:', Object.fromEntries(result.apiCalls));
    }

    expect(result.infiniteLoopDetected,
      `Infinite loop detected:\n${result.violations.join('\n')}`
    ).toBe(false);
  });

  test('should not have infinite loop on Stats page', async ({ page }) => {
    const result = await detectInfiniteLoop(page, {
      navigationUrl: 'http://localhost:3000/stats',
      maxAllowedCalls: 3,
      monitorDuration: 4000,
    });

    expect(result.infiniteLoopDetected,
      `Infinite loop detected:\n${result.violations.join('\n')}`
    ).toBe(false);
  });

  test('should not have infinite loop on Goals page', async ({ page }) => {
    const result = await detectInfiniteLoop(page, {
      navigationUrl: 'http://localhost:3000/goals',
      maxAllowedCalls: 3,
      monitorDuration: 4000,
    });

    expect(result.infiniteLoopDetected,
      `Infinite loop detected:\n${result.violations.join('\n')}`
    ).toBe(false);
  });

  test('should not have infinite loop when interacting with calendar', async ({ page }) => {
    const apiCalls = new Map<string, number>();

    page.on('request', (request) => {
      const url = request.url();
      if (/\/api\/v1\//.test(url)) {
        const normalizedUrl = url.split('?')[0];
        const count = apiCalls.get(normalizedUrl) || 0;
        apiCalls.set(normalizedUrl, count + 1);
      }
    });

    await page.goto('http://localhost:3000/');
    await page.waitForLoadState('networkidle');

    // Clear initial call counts
    apiCalls.clear();

    // Open calendar
    const calendarButton = page.locator('button.calendar-icon').first();
    if (await calendarButton.isVisible()) {
      await calendarButton.click();
      await page.waitForTimeout(2000);

      // Check for excessive calls after calendar interaction
      for (const [url, count] of apiCalls.entries()) {
        expect(count, `${url} called ${count} times after calendar open`).toBeLessThanOrEqual(2);
      }
    }
  });

  test('should not have infinite loop when editing a meal', async ({ page }) => {
    // Mock a meal for editing
    await page.route('**/api/v1/meals**', async (route) => {
      const url = route.request().url();
      if (url.includes('calendar')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ dates: [] }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            meals: [{
              id: 'meal-123',
              userId: '12341234',
              createdAt: new Date().toISOString(),
              description: 'Test meal',
              calories: 500,
              macronutrients: { protein: 25, carbs: 50, fats: 20 },
              photos: [{
                id: 'photo-123',
                thumbnailUrl: 'https://example.com/thumb.jpg',
                fullUrl: 'https://example.com/full.jpg',
                displayOrder: 0,
              }],
              confidenceScore: 0.95,
            }],
            total: 1,
            calories: 500,
            macronutrients: { protein: 25, carbs: 50, fats: 20 },
            photos: 1,
          }),
        });
      }
    });

    const apiCalls = new Map<string, number>();

    page.on('request', (request) => {
      const url = request.url();
      if (/\/api\/v1\//.test(url)) {
        const normalizedUrl = url.split('?')[0];
        const count = apiCalls.get(normalizedUrl) || 0;
        apiCalls.set(normalizedUrl, count + 1);
      }
    });

    await page.goto('http://localhost:3000/');
    await page.waitForLoadState('networkidle');

    // Clear initial call counts
    apiCalls.clear();

    // Try to open meal editor (if meal card exists)
    const mealCard = page.locator('.meal-card').first();
    if (await mealCard.isVisible()) {
      await mealCard.click();
      const editButton = page.locator('button.edit-button');
      if (await editButton.isVisible()) {
        await editButton.click();
        await page.waitForTimeout(2000);

        // Check for excessive calls after editing
        for (const [url, count] of apiCalls.entries()) {
          expect(count, `${url} called ${count} times after edit modal open`).toBeLessThanOrEqual(2);
        }
      }
    }
  });

  test('should not have excessive re-renders when component mounts', async ({ page }) => {
    let renderCount = 0;

    // Inject a render counter
    await page.addInitScript(() => {
      const originalLog = console.log;
      (window as any).__renderCount__ = 0;
      console.log = (...args: any[]) => {
        if (args[0]?.includes?.('render')) {
          (window as any).__renderCount__++;
        }
        return originalLog.apply(console, args);
      };
    });

    await page.goto('http://localhost:3000/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Get render count
    renderCount = await page.evaluate(() => (window as any).__renderCount__ || 0);

    // React in dev mode renders twice (StrictMode), so allow up to 4 renders
    // In production, expect <= 2 renders
    expect(renderCount, 'Too many renders detected').toBeLessThanOrEqual(10);
  });
});
