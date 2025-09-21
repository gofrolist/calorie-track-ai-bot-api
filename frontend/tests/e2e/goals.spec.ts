import { test, expect } from '@playwright/test';

test.describe('Goals Page', () => {
  const mockGoal = {
    user_id: 'user-1',
    daily_kcal_target: 2000,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  };

  const mockDailySummary = {
    user_id: 'user-1',
    date: '2024-01-15',
    kcal_total: 1500,
    macros_totals: {
      protein_g: 75,
      fat_g: 50,
      carbs_g: 150
    }
  };

  test('shows title and empty state when no goals set', async ({ page }) => {
    // Mock empty goals response
    await page.route('**/api/v1/goals', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(null),
      });
    });

    await page.goto('/goals');
    await expect(page.getByRole('heading', { name: 'Goals' })).toBeVisible();
    await expect(page.getByText('No goals set yet.')).toBeVisible();

    // Should show option to set goals
    await expect(page.getByRole('button', { name: 'Set Daily Goal' })).toBeVisible();
  });

  test('displays current goal and progress indicators', async ({ page }) => {
    // Mock goals API response
    await page.route('**/api/v1/goals', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockGoal),
      });
    });

    // Mock daily summary API response
    await page.route('**/api/v1/daily-summary/2024-01-15', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockDailySummary),
      });
    });

    await page.goto('/goals');

    // Check goal display
    await expect(page.getByText('Daily Calorie Goal')).toBeVisible();
    await expect(page.getByText('2000 kcal')).toBeVisible();

    // Check progress indicators
    await expect(page.getByText('Today\'s Progress')).toBeVisible();
    await expect(page.getByText('1500 / 2000 kcal')).toBeVisible();

    // Check progress percentage (75%)
    await expect(page.getByText('75%')).toBeVisible();

    // Check progress bar
    const progressBar = page.getByRole('progressbar');
    await expect(progressBar).toBeVisible();
    await expect(progressBar).toHaveAttribute('aria-valuenow', '75');
    await expect(progressBar).toHaveAttribute('aria-valuemax', '100');

    // Check calories remaining
    await expect(page.getByText('500 kcal remaining')).toBeVisible();
  });

  test('updates progress indicators when goal is achieved', async ({ page }) => {
    const achievedSummary = {
      ...mockDailySummary,
      kcal_total: 2000 // Exactly at goal
    };

    // Mock goals API response
    await page.route('**/api/v1/goals', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockGoal),
      });
    });

    // Mock daily summary API response with goal achieved
    await page.route('**/api/v1/daily-summary/2024-01-15', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(achievedSummary),
      });
    });

    await page.goto('/goals');

    // Check progress shows 100%
    await expect(page.getByText('2000 / 2000 kcal')).toBeVisible();
    await expect(page.getByText('100%')).toBeVisible();

    // Check progress bar is full
    const progressBar = page.getByRole('progressbar');
    await expect(progressBar).toHaveAttribute('aria-valuenow', '100');

    // Check goal achieved message
    await expect(page.getByText('Goal achieved!')).toBeVisible();
    await expect(page.getByText('0 kcal remaining')).toBeVisible();
  });

  test('updates progress indicators when goal is exceeded', async ({ page }) => {
    const exceededSummary = {
      ...mockDailySummary,
      kcal_total: 2200 // Over goal
    };

    // Mock goals API response
    await page.route('**/api/v1/goals', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockGoal),
      });
    });

    // Mock daily summary API response with goal exceeded
    await page.route('**/api/v1/daily-summary/2024-01-15', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(exceededSummary),
      });
    });

    await page.goto('/goals');

    // Check progress shows over 100%
    await expect(page.getByText('2200 / 2000 kcal')).toBeVisible();
    await expect(page.getByText('110%')).toBeVisible();

    // Check progress bar shows over goal
    const progressBar = page.getByRole('progressbar');
    await expect(progressBar).toHaveAttribute('aria-valuenow', '110');

    // Check over goal message
    await expect(page.getByText('200 kcal over goal')).toBeVisible();
  });

  test('allows editing daily calorie goal', async ({ page }) => {
    // Mock goals API response
    await page.route('**/api/v1/goals', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockGoal),
        });
      }
    });

    // Mock daily summary API response
    await page.route('**/api/v1/daily-summary/2024-01-15', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockDailySummary),
      });
    });

    await page.goto('/goals');

    // Check edit button is available
    const editButton = page.getByRole('button', { name: 'Edit Goal' });
    await expect(editButton).toBeVisible();

    // Click edit and check form appears
    await editButton.click();

    const goalInput = page.getByLabel('Daily Calorie Goal');
    await expect(goalInput).toBeVisible();
    await expect(goalInput).toHaveValue('2000');

    // Check save and cancel buttons
    await expect(page.getByRole('button', { name: 'Save' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
  });

  test('saves updated goal and refreshes progress indicators', async ({ page }) => {
    // Mock initial goals API response
    await page.route('**/api/v1/goals', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockGoal),
        });
      }
    });

    // Mock goal update API response
    let updateCalled = false;
    let updatedData = {};
    await page.route('**/api/v1/goals', async (route) => {
      if (route.request().method() === 'PUT' || route.request().method() === 'PATCH') {
        updateCalled = true;
        updatedData = await route.request().postDataJSON();

        const updatedGoal = {
          ...mockGoal,
          daily_kcal_target: updatedData.daily_kcal_target || mockGoal.daily_kcal_target,
          updated_at: '2024-01-15T10:05:00Z'
        };

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(updatedGoal),
        });
      }
    });

    // Mock daily summary API response
    await page.route('**/api/v1/daily-summary/2024-01-15', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockDailySummary),
      });
    });

    await page.goto('/goals');

    // Edit goal
    await page.getByRole('button', { name: 'Edit Goal' }).click();
    await page.getByLabel('Daily Calorie Goal').fill('1800');
    await page.getByRole('button', { name: 'Save' }).click();

    // Wait for save operation to complete
    await expect(page.getByText('Goal updated successfully')).toBeVisible();

    // Verify API was called with correct data
    expect(updateCalled).toBe(true);
    expect(updatedData.daily_kcal_target).toBe(1800);

    // Verify updated goal is displayed
    await expect(page.getByText('1800 kcal')).toBeVisible();

    // Verify progress recalculated (1500/1800 = 83.3%)
    await expect(page.getByText('1500 / 1800 kcal')).toBeVisible();
    await expect(page.getByText('83%')).toBeVisible();
  });

  test('shows loading state while fetching goal data', async ({ page }) => {
    // Mock delayed response
    await page.route('**/api/v1/goals', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockGoal),
      });
    });

    await page.goto('/goals');

    // Should show loading indicator
    await expect(page.getByText('Loading goals...')).toBeVisible();

    // Wait for loading to complete
    await expect(page.getByText('2000 kcal')).toBeVisible();
  });

  test('handles API errors gracefully', async ({ page }) => {
    // Mock error response
    await page.route('**/api/v1/goals', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    await page.goto('/goals');

    // Check for error message
    await expect(page.getByText('Failed to load goals. Please try again.')).toBeVisible();

    // Check for retry button
    await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible();
  });
});
