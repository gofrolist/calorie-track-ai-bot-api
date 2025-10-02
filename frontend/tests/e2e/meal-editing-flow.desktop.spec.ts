/**
 * E2E Test: Meal editing flow
 * Feature: 003-update-logic-for
 * Task: T057
 * Scenario 7: Meal editing
 */

import { test, expect } from '@playwright/test';

test.describe('Meal Editing Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/meals*', async (route) => {
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

  test('should open edit modal when edit button is clicked', async ({ page }) => {
    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click edit button
    await page.click('.meal-card:first-child .edit-button');

    // Edit modal should open
    await expect(page.locator('.meal-editor-modal')).toBeVisible();
    await expect(page.locator('.meal-editor-modal h2')).toContainText('Edit Meal');
  });

  test('should pre-fill form with current meal data', async ({ page }) => {
    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click edit button
    await page.click('.meal-card:first-child .edit-button');

    // Form should be pre-filled
    await expect(page.locator('input[name="description"]')).toHaveValue('Chicken pasta dinner');
    await expect(page.locator('input[name="protein_grams"]')).toHaveValue('45.5');
    await expect(page.locator('input[name="carbs_grams"]')).toHaveValue('75.0');
    await expect(page.locator('input[name="fats_grams"]')).toHaveValue('18.2');
  });

  test('should update meal description', async ({ page }) => {
    // Mock successful update response
    await page.route('**/api/v1/meals/meal-1', async (route) => {
      if (route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'meal-1',
            user_id: 'user-1',
            created_at: '2025-09-30T12:30:00Z',
            description: 'Updated: Grilled chicken pasta',
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
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click edit button
    await page.click('.meal-card:first-child .edit-button');

    // Update description
    await page.fill('input[name="description"]', 'Updated: Grilled chicken pasta');

    // Save changes
    await page.click('.meal-editor-modal .save-button');

    // Modal should close
    await expect(page.locator('.meal-editor-modal')).not.toBeVisible();

    // Meal card should show updated description
    await expect(page.locator('.meal-card:first-child .meal-description')).toContainText('Updated: Grilled chicken pasta');
  });

  test('should update macronutrients and recalculate calories', async ({ page }) => {
    // Mock successful update response with recalculated calories
    await page.route('**/api/v1/meals/meal-1', async (route) => {
      if (route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'meal-1',
            user_id: 'user-1',
            created_at: '2025-09-30T12:30:00Z',
            description: 'Chicken pasta dinner',
            calories: 660.0, // 50*4 + 70*4 + 20*9 = 660
            macronutrients: {
              protein: 50.0,
              carbs: 70.0,
              fats: 20.0,
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
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click edit button
    await page.click('.meal-card:first-child .edit-button');

    // Update macronutrients
    await page.fill('input[name="protein_grams"]', '50');
    await page.fill('input[name="carbs_grams"]', '70');
    await page.fill('input[name="fats_grams"]', '20');

    // Save changes
    await page.click('.meal-editor-modal .save-button');

    // Modal should close
    await expect(page.locator('.meal-editor-modal')).not.toBeVisible();

    // Meal card should show updated values
    await expect(page.locator('.meal-card:first-child .meal-calories')).toContainText('660');
    await expect(page.locator('.meal-card:first-child .macro-item').nth(0)).toContainText('50.0g');
    await expect(page.locator('.meal-card:first-child .macro-item').nth(1)).toContainText('70.0g');
    await expect(page.locator('.meal-card:first-child .macro-item').nth(2)).toContainText('20.0g');
  });

  test('should show optimistic update before server response', async ({ page }) => {
    // Mock delayed update response
    await page.route('**/api/v1/meals/meal-1', async (route) => {
      if (route.request().method() === 'PATCH') {
        // Delay response to test optimistic update
        await new Promise(resolve => setTimeout(resolve, 1000));
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'meal-1',
            user_id: 'user-1',
            created_at: '2025-09-30T12:30:00Z',
            description: 'Updated: Grilled chicken pasta',
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
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click edit button
    await page.click('.meal-card:first-child .edit-button');

    // Update description
    await page.fill('input[name="description"]', 'Updated: Grilled chicken pasta');

    // Save changes
    await page.click('.meal-editor-modal .save-button');

    // Modal should close immediately (optimistic update)
    await expect(page.locator('.meal-editor-modal')).not.toBeVisible();

    // Meal card should show updated description immediately
    await expect(page.locator('.meal-card:first-child .meal-description')).toContainText('Updated: Grilled chicken pasta');
  });

  test('should revert changes on update failure', async ({ page }) => {
    // Mock failed update response
    await page.route('**/api/v1/meals/meal-1', async (route) => {
      if (route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Internal server error',
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click edit button
    await page.click('.meal-card:first-child .edit-button');

    // Update description
    await page.fill('input[name="description"]', 'Updated: Grilled chicken pasta');

    // Save changes
    await page.click('.meal-editor-modal .save-button');

    // Modal should close
    await expect(page.locator('.meal-editor-modal')).not.toBeVisible();

    // Should show error message
    await expect(page.locator('.error-message')).toContainText('Failed to update meal');

    // Meal card should revert to original description
    await expect(page.locator('.meal-card:first-child .meal-description')).toContainText('Chicken pasta dinner');
  });

  test('should validate form inputs', async ({ page }) => {
    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click edit button
    await page.click('.meal-card:first-child .edit-button');

    // Try to enter negative values
    await page.fill('input[name="protein_grams"]', '-10');
    await page.fill('input[name="carbs_grams"]', '-5');
    await page.fill('input[name="fats_grams"]', '-2');

    // Save changes
    await page.click('.meal-editor-modal .save-button');

    // Should show validation errors
    await expect(page.locator('.validation-error')).toContainText('Macronutrients must be positive');

    // Modal should remain open
    await expect(page.locator('.meal-editor-modal')).toBeVisible();
  });

  test('should cancel editing without saving', async ({ page }) => {
    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click edit button
    await page.click('.meal-card:first-child .edit-button');

    // Make changes
    await page.fill('input[name="description"]', 'This should not be saved');

    // Click cancel
    await page.click('.meal-editor-modal .cancel-button');

    // Modal should close
    await expect(page.locator('.meal-editor-modal')).not.toBeVisible();

    // Meal card should show original description
    await expect(page.locator('.meal-card:first-child .meal-description')).toContainText('Chicken pasta dinner');
  });

  test('should handle empty description', async ({ page }) => {
    // Mock successful update response with empty description
    await page.route('**/api/v1/meals/meal-1', async (route) => {
      if (route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'meal-1',
            user_id: 'user-1',
            created_at: '2025-09-30T12:30:00Z',
            description: null,
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
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click edit button
    await page.click('.meal-card:first-child .edit-button');

    // Clear description
    await page.fill('input[name="description"]', '');

    // Save changes
    await page.click('.meal-editor-modal .save-button');

    // Modal should close
    await expect(page.locator('.meal-editor-modal')).not.toBeVisible();

    // Meal card should show placeholder for empty description
    await expect(page.locator('.meal-card:first-child .meal-description')).toContainText('No description');
  });

  test('should be keyboard accessible', async ({ page }) => {
    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Focus edit button and press Enter
    await page.focus('.meal-card:first-child .edit-button');
    await page.keyboard.press('Enter');

    // Edit modal should open
    await expect(page.locator('.meal-editor-modal')).toBeVisible();

    // Tab through form fields
    await page.keyboard.press('Tab'); // description
    await page.keyboard.press('Tab'); // protein
    await page.keyboard.press('Tab'); // carbs
    await page.keyboard.press('Tab'); // fats
    await page.keyboard.press('Tab'); // save button

    // Press Escape to close modal
    await page.keyboard.press('Escape');

    // Modal should close
    await expect(page.locator('.meal-editor-modal')).not.toBeVisible();
  });

  test('should work on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click edit button
    await page.click('.meal-card:first-child .edit-button');

    // Modal should be mobile-friendly
    await expect(page.locator('.meal-editor-modal')).toBeVisible();

    // Form should be scrollable on mobile
    const modal = page.locator('.meal-editor-modal');
    const isScrollable = await modal.evaluate((el) => {
      return el.scrollHeight > el.clientHeight;
    });

    // Should be scrollable if content is too tall
    expect(isScrollable).toBe(true);
  });
});
