import { test, expect } from '@playwright/test';

test.describe('Meal Detail Page', () => {
  const mockMeal = {
    id: 'meal-123',
    user_id: 'user-1',
    meal_date: '2024-01-15',
    meal_type: 'lunch',
    kcal_total: 550,
    macros: {
      protein_g: 25,
      fat_g: 20,
      carbs_g: 45
    },
    estimate_id: 'est-1',
    corrected: false,
    created_at: '2024-01-15T13:00:00Z',
    updated_at: '2024-01-15T13:00:00Z'
  };

  test('displays meal details and allows corrections', async ({ page }) => {
    // Mock meal detail API response
    await page.route('**/api/v1/meals/meal-123', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockMeal),
      });
    });

    await page.goto('/meal/meal-123');

    // Check that meal details are displayed
    await expect(page.getByRole('heading', { name: 'Meal Detail' })).toBeVisible();
    await expect(page.getByText('Lunch')).toBeVisible();
    await expect(page.getByText('550 kcal')).toBeVisible();
    await expect(page.getByText('25g protein')).toBeVisible();
    await expect(page.getByText('20g fat')).toBeVisible();
    await expect(page.getByText('45g carbs')).toBeVisible();

    // Check for edit/correction functionality
    const editButton = page.getByRole('button', { name: 'Edit' });
    await expect(editButton).toBeVisible();
  });

  test('allows editing calories and macros', async ({ page }) => {
    // Mock meal detail API response
    await page.route('**/api/v1/meals/meal-123', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockMeal),
      });
    });

    await page.goto('/meal/meal-123');

    // Enter edit mode
    await page.getByRole('button', { name: 'Edit' }).click();

    // Check that form fields are visible and editable
    const caloriesInput = page.getByLabel('Calories');
    const proteinInput = page.getByLabel('Protein (g)');
    const fatInput = page.getByLabel('Fat (g)');
    const carbsInput = page.getByLabel('Carbs (g)');

    await expect(caloriesInput).toBeVisible();
    await expect(proteinInput).toBeVisible();
    await expect(fatInput).toBeVisible();
    await expect(carbsInput).toBeVisible();

    // Check current values are populated
    await expect(caloriesInput).toHaveValue('550');
    await expect(proteinInput).toHaveValue('25');
    await expect(fatInput).toHaveValue('20');
    await expect(carbsInput).toHaveValue('45');

    // Modify values
    await caloriesInput.fill('600');
    await proteinInput.fill('30');
    await fatInput.fill('22');
    await carbsInput.fill('50');

    // Check save and cancel buttons are available
    await expect(page.getByRole('button', { name: 'Save' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
  });

  test('saves corrections and updates meal data', async ({ page }) => {
    // Mock initial meal detail API response
    await page.route('**/api/v1/meals/meal-123', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockMeal),
        });
      }
    });

    // Mock meal update API response
    let updateCalled = false;
    let updatedData = {};
    await page.route('**/api/v1/meals/meal-123', async (route) => {
      if (route.request().method() === 'PUT' || route.request().method() === 'PATCH') {
        updateCalled = true;
        updatedData = await route.request().postDataJSON();

        const updatedMeal = {
          ...mockMeal,
          kcal_total: updatedData.kcal_total || mockMeal.kcal_total,
          macros: {
            ...mockMeal.macros,
            ...updatedData.macros
          },
          corrected: true,
          updated_at: '2024-01-15T13:05:00Z'
        };

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(updatedMeal),
        });
      }
    });

    await page.goto('/meal/meal-123');

    // Enter edit mode and modify values
    await page.getByRole('button', { name: 'Edit' }).click();

    await page.getByLabel('Calories').fill('600');
    await page.getByLabel('Protein (g)').fill('30');

    // Save changes
    await page.getByRole('button', { name: 'Save' }).click();

    // Wait for save operation to complete
    await expect(page.getByText('Meal updated successfully')).toBeVisible();

    // Verify updated values are displayed
    await expect(page.getByText('600 kcal')).toBeVisible();
    await expect(page.getByText('30g protein')).toBeVisible();

    // Verify the meal is marked as corrected
    await expect(page.getByText('Corrected')).toBeVisible();

    // Verify API was called with correct data
    expect(updateCalled).toBe(true);
    expect(updatedData.kcal_total).toBe(600);
    expect(updatedData.macros.protein_g).toBe(30);
  });

  test('handles canceling edit mode', async ({ page }) => {
    // Mock meal detail API response
    await page.route('**/api/v1/meals/meal-123', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockMeal),
      });
    });

    await page.goto('/meal/meal-123');

    // Enter edit mode
    await page.getByRole('button', { name: 'Edit' }).click();

    // Modify a value
    await page.getByLabel('Calories').fill('999');

    // Cancel changes
    await page.getByRole('button', { name: 'Cancel' }).click();

    // Verify original values are still displayed
    await expect(page.getByText('550 kcal')).toBeVisible();

    // Verify edit mode is exited
    await expect(page.getByRole('button', { name: 'Edit' })).toBeVisible();
    await expect(page.getByLabel('Calories')).not.toBeVisible();
  });

  test('shows validation errors for invalid input', async ({ page }) => {
    // Mock meal detail API response
    await page.route('**/api/v1/meals/meal-123', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockMeal),
      });
    });

    await page.goto('/meal/meal-123');

    // Enter edit mode
    await page.getByRole('button', { name: 'Edit' }).click();

    // Enter invalid values
    await page.getByLabel('Calories').fill('-100');
    await page.getByLabel('Protein (g)').fill('abc');

    // Try to save
    await page.getByRole('button', { name: 'Save' }).click();

    // Check for validation errors
    await expect(page.getByText('Calories must be a positive number')).toBeVisible();
    await expect(page.getByText('Protein must be a valid number')).toBeVisible();
  });

  test('handles API errors during save', async ({ page }) => {
    // Mock meal detail API response
    await page.route('**/api/v1/meals/meal-123', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockMeal),
        });
      } else if (route.request().method() === 'PUT' || route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal server error' }),
        });
      }
    });

    await page.goto('/meal/meal-123');

    // Enter edit mode and modify values
    await page.getByRole('button', { name: 'Edit' }).click();
    await page.getByLabel('Calories').fill('600');

    // Try to save
    await page.getByRole('button', { name: 'Save' }).click();

    // Check for error message
    await expect(page.getByText('Failed to save changes. Please try again.')).toBeVisible();

    // Verify still in edit mode
    await expect(page.getByLabel('Calories')).toBeVisible();
  });

  test('shows loading state while fetching meal details', async ({ page }) => {
    // Mock delayed response
    await page.route('**/api/v1/meals/meal-123', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockMeal),
      });
    });

    await page.goto('/meal/meal-123');

    // Should show loading indicator
    await expect(page.getByText('Loading meal details...')).toBeVisible();

    // Wait for loading to complete
    await expect(page.getByText('550 kcal')).toBeVisible();
  });

  test('handles meal not found error', async ({ page }) => {
    // Mock 404 response
    await page.route('**/api/v1/meals/nonexistent', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Meal not found' }),
      });
    });

    await page.goto('/meal/nonexistent');

    // Check for error message
    await expect(page.getByText('Meal not found')).toBeVisible();

    // Check for back to today link
    await expect(page.getByRole('link', { name: 'Back to Today' })).toBeVisible();
  });

  test('allows deletion of meal', async ({ page }) => {
    // Mock meal detail API response
    await page.route('**/api/v1/meals/meal-123', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockMeal),
        });
      }
    });

    // Mock delete API response
    let deleteCalled = false;
    await page.route('**/api/v1/meals/meal-123', async (route) => {
      if (route.request().method() === 'DELETE') {
        deleteCalled = true;
        await route.fulfill({
          status: 204,
          contentType: 'application/json',
          body: '',
        });
      }
    });

    await page.goto('/meal/meal-123');

    // Check delete button is available
    const deleteButton = page.getByRole('button', { name: 'Delete' });
    await expect(deleteButton).toBeVisible();

    // Click delete and confirm
    await deleteButton.click();

    // Check for confirmation dialog
    await expect(page.getByText('Are you sure you want to delete this meal?')).toBeVisible();
    await page.getByRole('button', { name: 'Confirm Delete' }).click();

    // Verify API was called
    expect(deleteCalled).toBe(true);

    // Should show success message and redirect
    await expect(page.getByText('Meal deleted successfully')).toBeVisible();
  });
});
