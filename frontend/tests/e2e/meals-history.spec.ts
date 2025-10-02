/**
 * E2E Test: Calendar-based meal history
 * Feature: 003-update-logic-for
 * Task: T043
 * Scenario 4: Calendar-based meal history (Mini-App)
 */

import { test, expect } from '@playwright/test';

test.describe('Meals History - Calendar Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
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
                photos: [],
                confidence_score: 0.90,
              },
            ],
            total: 1,
          }),
        });
      } else {
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

    await page.route('**/api/v1/meals/calendar*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          dates: [
            {
              date: '2025-09-30',
              meal_count: 1,
              total_calories: 650.0,
              total_protein: 45.5,
              total_carbs: 75.0,
              total_fats: 18.2,
            },
            {
              date: '2025-09-25',
              meal_count: 1,
              total_calories: 320.0,
              total_protein: 15.0,
              total_carbs: 45.0,
              total_fats: 8.0,
            },
          ],
        }),
      });
    });

    // Navigate to meals page
    await page.goto('/');
  });

  test('should show today\'s meals by default', async ({ page }) => {
    // Page title should show "Meals" (not "Today")
    await expect(page.locator('h1')).toContainText('Meals');

    // Should show today's date
    const today = new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    await expect(page.locator('[data-testid="selected-date"]')).toContainText(today);

    // Should show today's meal
    await expect(page.locator('.meal-card')).toHaveCount(1);
    await expect(page.locator('.meal-card')).toContainText('Chicken pasta dinner');
    await expect(page.locator('.meal-card')).toContainText('650 kcal');
  });

  test('should open calendar picker when calendar icon is clicked', async ({ page }) => {
    // Click calendar icon
    await page.click('[data-testid="calendar-button"]');

    // Calendar should be visible
    await expect(page.locator('.calendar-picker')).toBeVisible();

    // Should show calendar with today selected
    await expect(page.locator('.rdp-day_selected')).toBeVisible();
  });

  test('should show dates with meal indicators', async ({ page }) => {
    // Open calendar
    await page.click('[data-testid="calendar-button"]');

    // Dates with meals should have special styling
    const datesWithMeals = page.locator('.rdp-day[data-has-data="true"]');
    await expect(datesWithMeals).toHaveCount(2); // 2025-09-30 and 2025-09-25
  });

  test('should disable future dates', async ({ page }) => {
    // Open calendar
    await page.click('[data-testid="calendar-button"]');

    // Future dates should be disabled
    const futureDate = page.locator('.rdp-day_disabled').first();
    await expect(futureDate).toBeVisible();
  });

  test('should disable dates older than 1 year', async ({ page }) => {
    // Open calendar
    await page.click('[data-testid="calendar-button"]');

    // Navigate to previous year
    await page.click('.rdp-nav_button_previous');
    await page.click('.rdp-nav_button_previous');

    // Old dates should be disabled
    const oldDates = page.locator('.rdp-day_disabled');
    await expect(oldDates).toHaveCount(31); // All days in old month should be disabled
  });

  test('should load meals for selected date', async ({ page }) => {
    // Open calendar
    await page.click('[data-testid="calendar-button"]');

    // Click on September 25th
    await page.click('[data-day="25"]');

    // Calendar should close
    await expect(page.locator('.calendar-picker')).not.toBeVisible();

    // Should show meals for September 25th
    await expect(page.locator('.meal-card')).toHaveCount(1);
    await expect(page.locator('.meal-card')).toContainText('Breakfast smoothie');
    await expect(page.locator('.meal-card')).toContainText('320 kcal');

    // Date display should update
    await expect(page.locator('[data-testid="selected-date"]')).toContainText('September 25, 2025');
  });

  test('should show no data message for dates without meals', async ({ page }) => {
    // Open calendar
    await page.click('[data-testid="calendar-button"]');

    // Click on a date without meals (e.g., September 26th)
    await page.click('[data-day="26"]');

    // Should show no meals message
    await expect(page.locator('[data-testid="no-meals-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="no-meals-message"]')).toContainText('No meals found for this date');
  });

  test('should close calendar when clicking outside', async ({ page }) => {
    // Open calendar
    await page.click('[data-testid="calendar-button"]');
    await expect(page.locator('.calendar-picker')).toBeVisible();

    // Click outside calendar
    await page.click('body', { position: { x: 10, y: 10 } });

    // Calendar should close
    await expect(page.locator('.calendar-picker')).not.toBeVisible();
  });

  test('should handle keyboard navigation in calendar', async ({ page }) => {
    // Open calendar
    await page.click('[data-testid="calendar-button"]');

    // Focus on calendar
    await page.keyboard.press('Tab');

    // Navigate with arrow keys
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('ArrowDown');

    // Select with Enter
    await page.keyboard.press('Enter');

    // Calendar should close and date should change
    await expect(page.locator('.calendar-picker')).not.toBeVisible();
  });

  test('should show quick navigation buttons', async ({ page }) => {
    // Should have "Today" button
    await expect(page.locator('[data-testid="today-button"]')).toBeVisible();

    // Should have "This Week" button
    await expect(page.locator('[data-testid="this-week-button"]')).toBeVisible();
  });

  test('should navigate to today when Today button is clicked', async ({ page }) => {
    // First navigate to a different date
    await page.click('[data-testid="calendar-button"]');
    await page.click('[data-day="25"]');

    // Click Today button
    await page.click('[data-testid="today-button"]');

    // Should show today's meals
    await expect(page.locator('.meal-card')).toContainText('Chicken pasta dinner');

    // Date should be today
    const today = new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
    await expect(page.locator('[data-testid="selected-date"]')).toContainText(today);
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Calendar should still be functional
    await page.click('[data-testid="calendar-button"]');
    await expect(page.locator('.calendar-picker')).toBeVisible();

    // Touch targets should be at least 44px
    const calendarButtons = page.locator('.rdp-day button');
    const firstButton = calendarButtons.first();
    const box = await firstButton.boundingBox();
    expect(box?.height).toBeGreaterThanOrEqual(44);
    expect(box?.width).toBeGreaterThanOrEqual(44);
  });
});
