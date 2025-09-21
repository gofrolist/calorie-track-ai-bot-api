import { test, expect } from '@playwright/test';

test.describe('Today View', () => {
  test('shows title and empty state when no meals', async ({ page }) => {
    // Mock empty meals response
    await page.route('**/api/v1/meals**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ meals: [], total_calories: 0 }),
      });
    });

    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Today' })).toBeVisible();
    await expect(page.getByText('No meals yet. Send a photo to the bot to start.')).toBeVisible();
    await expect(page.getByText('Total: 0 kcal')).toBeVisible();
  });

  test('lists meals and shows daily totals', async ({ page }) => {
    // Mock meals response with sample data
    const mockMeals = [
      {
        id: 'meal-1',
        meal_date: '2024-01-15',
        meal_type: 'breakfast',
        kcal_total: 350,
        source: 'manual',
        created_at: '2024-01-15T08:00:00Z',
      },
      {
        id: 'meal-2',
        meal_date: '2024-01-15',
        meal_type: 'lunch',
        kcal_total: 550,
        source: 'estimate',
        estimate_id: 'est-1',
        created_at: '2024-01-15T13:00:00Z',
      },
      {
        id: 'meal-3',
        meal_date: '2024-01-15',
        meal_type: 'dinner',
        kcal_total: 600,
        source: 'manual',
        created_at: '2024-01-15T19:00:00Z',
      },
      {
        id: 'meal-4',
        meal_date: '2024-01-15',
        meal_type: 'snack',
        kcal_total: 150,
        source: 'estimate',
        estimate_id: 'est-2',
        created_at: '2024-01-15T16:00:00Z',
      },
    ];

    await page.route('**/api/v1/meals**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          meals: mockMeals,
          total_calories: 1650
        }),
      });
    });

    await page.goto('/');

    // Check title
    await expect(page.getByRole('heading', { name: 'Today' })).toBeVisible();

    // Check total calories
    await expect(page.getByText('Total: 1,650 kcal')).toBeVisible();

    // Check meal types are displayed
    await expect(page.getByText('Breakfast')).toBeVisible();
    await expect(page.getByText('Lunch')).toBeVisible();
    await expect(page.getByText('Dinner')).toBeVisible();
    await expect(page.getByText('Snack')).toBeVisible();

    // Check individual meal calories
    await expect(page.getByText('350 kcal')).toBeVisible();
    await expect(page.getByText('550 kcal')).toBeVisible();
    await expect(page.getByText('600 kcal')).toBeVisible();
    await expect(page.getByText('150 kcal')).toBeVisible();

    // Check that meals are clickable (should navigate to meal detail)
    const breakfastMeal = page.getByText('Breakfast').locator('..');
    await expect(breakfastMeal).toBeVisible();

    // Verify meal items have proper structure
    const mealItems = page.locator('[data-testid="meal-item"]');
    await expect(mealItems).toHaveCount(4);
  });

  test('handles API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/meals**', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    await page.goto('/');

    // Should still show title
    await expect(page.getByRole('heading', { name: 'Today' })).toBeVisible();

    // Should show error state
    await expect(page.getByText('Failed to load meals')).toBeVisible();
  });

  test('shows loading state while fetching meals', async ({ page }) => {
    // Mock delayed response
    await page.route('**/api/v1/meals**', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ meals: [], total_calories: 0 }),
      });
    });

    await page.goto('/');

    // Should show loading indicator
    await expect(page.getByText('Loading...')).toBeVisible();

    // Wait for loading to complete
    await expect(page.getByText('No meals yet. Send a photo to the bot to start.')).toBeVisible();
  });
});
