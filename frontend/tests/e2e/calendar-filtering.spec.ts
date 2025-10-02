/**
 * E2E Test: Calendar date filtering
 * Feature: 003-update-logic-for
 * Task: T060
 * Test calendar date filtering functionality
 */

import { test, expect } from '@playwright/test';

test.describe('Calendar Date Filtering', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses for different dates
    await page.route('**/api/v1/meals*', async (route) => {
      const url = new URL(route.request().url());
      const date = url.searchParams.get('date');

      if (date === '2025-09-30') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            meals: [
              {
                id: 'meal-1',
                user_id: 'user-1',
                created_at: '2025-09-30T12:30:00Z',
                description: 'Chicken pasta dinner',
                calories: 650.0,
                macronutrients: {
                  protein: 45.5,
                  carbs: 75.0,
                  fats: 18.2,
                },
                photos: [
                  {
                    id: 'photo-1',
                    thumbnail_url: 'https://example.com/thumb1.jpg',
                    full_url: 'https://example.com/full1.jpg',
                    display_order: 0,
                  },
                ],
                confidence_score: 0.85,
              },
            ],
            total: 1,
          }),
        });
      } else if (date === '2025-09-25') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            meals: [
              {
                id: 'meal-2',
                user_id: 'user-1',
                created_at: '2025-09-25T08:15:00Z',
                description: 'Breakfast smoothie',
                calories: 320.0,
                macronutrients: {
                  protein: 15.0,
                  carbs: 45.0,
                  fats: 8.0,
                },
                photos: [
                  {
                    id: 'photo-2',
                    thumbnail_url: 'https://example.com/thumb2.jpg',
                    full_url: 'https://example.com/full2.jpg',
                    display_order: 0,
                  },
                ],
                confidence_score: 0.90,
              },
              {
                id: 'meal-3',
                user_id: 'user-1',
                created_at: '2025-09-25T18:30:00Z',
                description: 'Grilled salmon',
                calories: 450.0,
                macronutrients: {
                  protein: 35.0,
                  carbs: 20.0,
                  fats: 25.0,
                },
                photos: [
                  {
                    id: 'photo-3',
                    thumbnail_url: 'https://example.com/thumb3.jpg',
                    full_url: 'https://example.com/full3.jpg',
                    display_order: 0,
                  },
                ],
                confidence_score: 0.88,
              },
            ],
            total: 2,
          }),
        });
      } else if (date === '2025-09-20') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            meals: [],
            total: 0,
          }),
        });
      } else {
        // Default response for other dates
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            meals: [],
            total: 0,
          }),
        });
      }
    });

    // Mock calendar API response
    await page.route('**/api/v1/meals/calendar*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          dates: [
            {
              meal_date: '2025-09-30',
              meal_count: 1,
              total_calories: 650.0,
              total_protein: 45.5,
              total_carbs: 75.0,
              total_fats: 18.2,
            },
            {
              meal_date: '2025-09-25',
              meal_count: 2,
              total_calories: 770.0,
              total_protein: 50.0,
              total_carbs: 65.0,
              total_fats: 33.0,
            },
          ],
        }),
      });
    });

    // Mock image loading
    await page.route('**/example.com/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'image/jpeg',
        body: Buffer.from('fake-image-data'),
      });
    });

    await page.goto('/');
  });

  test('should show today\'s meals by default', async ({ page }) => {
    // Should show today's date in the header
    const today = new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    await expect(page.locator('.date-header')).toContainText(today);

    // Should show meals for today (mocked as 2025-09-30)
    await expect(page.locator('.meal-card')).toHaveCount(1);
    await expect(page.locator('.meal-card:first-child .meal-description')).toContainText('Chicken pasta dinner');
  });

  test('should open calendar picker when calendar icon is clicked', async ({ page }) => {
    // Click calendar icon
    await page.click('.calendar-icon');

    // Calendar picker should open
    await expect(page.locator('.calendar-picker')).toBeVisible();
    await expect(page.locator('.calendar-picker h3')).toContainText('Select Date');
  });

  test('should filter meals by selected date', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Select September 25, 2025
    await page.click('.calendar-picker [data-date="2025-09-25"]');

    // Calendar should close
    await expect(page.locator('.calendar-picker')).not.toBeVisible();

    // Should show meals for September 25
    await expect(page.locator('.date-header')).toContainText('September 25, 2025');
    await expect(page.locator('.meal-card')).toHaveCount(2);
    await expect(page.locator('.meal-card:first-child .meal-description')).toContainText('Breakfast smoothie');
    await expect(page.locator('.meal-card:nth-child(2) .meal-description')).toContainText('Grilled salmon');
  });

  test('should show empty state for dates with no meals', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Select September 20, 2025 (no meals)
    await page.click('.calendar-picker [data-date="2025-09-20"]');

    // Calendar should close
    await expect(page.locator('.calendar-picker')).not.toBeVisible();

    // Should show empty state
    await expect(page.locator('.date-header')).toContainText('September 20, 2025');
    await expect(page.locator('.empty-state')).toBeVisible();
    await expect(page.locator('.empty-state h3')).toContainText('No meals found');
    await expect(page.locator('.empty-state p')).toContainText('No meals recorded for this date');
  });

  test('should show visual indicators on dates with meals', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Dates with meals should have indicators
    await expect(page.locator('.calendar-picker [data-date="2025-09-30"] .meal-indicator')).toBeVisible();
    await expect(page.locator('.calendar-picker [data-date="2025-09-25"] .meal-indicator')).toBeVisible();

    // Date without meals should not have indicator
    await expect(page.locator('.calendar-picker [data-date="2025-09-20"] .meal-indicator')).not.toBeVisible();
  });

  test('should disable future dates', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Future dates should be disabled
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split('T')[0];

    await expect(page.locator(`.calendar-picker [data-date="${tomorrowStr}"]`)).toHaveClass(/disabled/);
  });

  test('should disable dates older than 1 year', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Date older than 1 year should be disabled
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
    oneYearAgo.setDate(oneYearAgo.getDate() - 1);
    const oneYearAgoStr = oneYearAgo.toISOString().split('T')[0];

    await expect(page.locator(`.calendar-picker [data-date="${oneYearAgoStr}"]`)).toHaveClass(/disabled/);
  });

  test('should show quick navigation buttons', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Should have quick navigation buttons
    await expect(page.locator('.calendar-picker .quick-nav .today-button')).toBeVisible();
    await expect(page.locator('.calendar-picker .quick-nav .yesterday-button')).toBeVisible();
    await expect(page.locator('.calendar-picker .quick-nav .this-week-button')).toBeVisible();
  });

  test('should navigate to today when today button is clicked', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Click today button
    await page.click('.calendar-picker .quick-nav .today-button');

    // Calendar should close
    await expect(page.locator('.calendar-picker')).not.toBeVisible();

    // Should show today's meals
    const today = new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    await expect(page.locator('.date-header')).toContainText(today);
  });

  test('should navigate to yesterday when yesterday button is clicked', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Click yesterday button
    await page.click('.calendar-picker .quick-nav .yesterday-button');

    // Calendar should close
    await expect(page.locator('.calendar-picker')).not.toBeVisible();

    // Should show yesterday's date
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = yesterday.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    await expect(page.locator('.date-header')).toContainText(yesterdayStr);
  });

  test('should close calendar when clicking outside', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Click outside the calendar
    await page.click('.calendar-picker', { position: { x: -10, y: -10 } });

    // Calendar should close
    await expect(page.locator('.calendar-picker')).not.toBeVisible();
  });

  test('should close calendar when pressing Escape key', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Press Escape key
    await page.keyboard.press('Escape');

    // Calendar should close
    await expect(page.locator('.calendar-picker')).not.toBeVisible();
  });

  test('should be keyboard accessible', async ({ page }) => {
    // Focus calendar icon and press Enter
    await page.focus('.calendar-icon');
    await page.keyboard.press('Enter');

    // Calendar should open
    await expect(page.locator('.calendar-picker')).toBeVisible();

    // Tab through calendar
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Press Enter on a date
    await page.keyboard.press('Enter');

    // Calendar should close
    await expect(page.locator('.calendar-picker')).not.toBeVisible();
  });

  test('should work on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Open calendar picker
    await page.click('.calendar-icon');

    // Calendar should be mobile-friendly
    await expect(page.locator('.calendar-picker')).toBeVisible();

    // Touch targets should be at least 44px
    const dateButton = page.locator('.calendar-picker [data-date="2025-09-25"]');
    const box = await dateButton.boundingBox();
    expect(box?.height).toBeGreaterThanOrEqual(44);
    expect(box?.width).toBeGreaterThanOrEqual(44);

    // Should work with touch
    await dateButton.tap();
    await expect(page.locator('.calendar-picker')).not.toBeVisible();
  });

  test('should show loading state while fetching meals', async ({ page }) => {
    // Mock delayed API response
    await page.route('**/api/v1/meals*', async (route) => {
      // Delay response
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          meals: [],
          total: 0,
        }),
      });
    });

    // Open calendar picker
    await page.click('.calendar-icon');

    // Select a date
    await page.click('.calendar-picker [data-date="2025-09-20"]');

    // Should show loading state
    await expect(page.locator('.loading-spinner')).toBeVisible();

    // Loading should disappear after response
    await expect(page.locator('.loading-spinner')).not.toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/meals*', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Internal server error',
        }),
      });
    });

    // Open calendar picker
    await page.click('.calendar-icon');

    // Select a date
    await page.click('.calendar-picker [data-date="2025-09-20"]');

    // Should show error message
    await expect(page.locator('.error-message')).toContainText('Failed to fetch meals');

    // Should still show the selected date
    await expect(page.locator('.date-header')).toContainText('September 20, 2025');
  });

  test('should maintain selected date across page refreshes', async ({ page }) => {
    // Select a specific date
    await page.click('.calendar-icon');
    await page.click('.calendar-picker [data-date="2025-09-25"]');

    // Verify date is selected
    await expect(page.locator('.date-header')).toContainText('September 25, 2025');

    // Refresh page
    await page.reload();

    // Should still show the selected date
    await expect(page.locator('.date-header')).toContainText('September 25, 2025');
  });

  test('should show meal count in calendar indicators', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Should show meal count in indicators
    await expect(page.locator('.calendar-picker [data-date="2025-09-30"] .meal-indicator')).toContainText('1');
    await expect(page.locator('.calendar-picker [data-date="2025-09-25"] .meal-indicator')).toContainText('2');
  });

  test('should highlight current selected date in calendar', async ({ page }) => {
    // Open calendar picker
    await page.click('.calendar-icon');

    // Today's date should be highlighted
    const today = new Date().toISOString().split('T')[0];
    await expect(page.locator(`.calendar-picker [data-date="${today}"]`)).toHaveClass(/selected/);
  });
});
