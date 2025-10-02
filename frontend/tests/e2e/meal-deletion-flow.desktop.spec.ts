/**
 * E2E Test: Meal deletion flow
 * Feature: 003-update-logic-for
 * Task: T058
 * Scenario 8: Meal deletion
 */

import { test, expect } from '@playwright/test';

test.describe('Meal Deletion Flow', () => {
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
                  thumbnailUrl: 'https://example.com/thumb1.jpg',
                  fullUrl: 'https://example.com/full1.jpg',
                  displayOrder: 0,
                },
              ],
              confidence_score: 0.85,
            },
            {
              id: 'meal-2',
              user_id: 'user-1',
              created_at: '2025-09-30T08:15:00Z',
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
                  thumbnailUrl: 'https://example.com/thumb2.jpg',
                  fullUrl: 'https://example.com/full2.jpg',
                  displayOrder: 0,
                },
              ],
              confidence_score: 0.90,
            },
          ],
          total: 2,
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

  test('should show delete button when meal is expanded', async ({ page }) => {
    // Expand first meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Delete button should be visible
    await expect(page.locator('.meal-card:first-child .delete-button')).toBeVisible();
    await expect(page.locator('.meal-card:first-child .delete-button')).toContainText('🗑️ Delete');
  });

  test('should show confirmation dialog when delete button is clicked', async ({ page }) => {
    // Expand first meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click delete button
    await page.click('.meal-card:first-child .delete-button');

    // Confirmation dialog should appear
    await expect(page.locator('.confirmation-dialog')).toBeVisible();
    await expect(page.locator('.confirmation-dialog h3')).toContainText('Delete Meal');
    await expect(page.locator('.confirmation-dialog p')).toContainText('Are you sure you want to delete this meal?');

    // Should have confirm and cancel buttons
    await expect(page.locator('.confirmation-dialog .confirm-button')).toBeVisible();
    await expect(page.locator('.confirmation-dialog .cancel-button')).toBeVisible();
  });

  test('should delete meal when confirmed', async ({ page }) => {
    // Mock successful deletion response
    await page.route('**/api/v1/meals/meal-1', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 204,
        });
      } else {
        await route.continue();
      }
    });

    // Mock updated meals list after deletion
    await page.route('**/api/v1/meals*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          meals: [
            {
              id: 'meal-2',
              user_id: 'user-1',
              created_at: '2025-09-30T08:15:00Z',
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
                  thumbnailUrl: 'https://example.com/thumb2.jpg',
                  fullUrl: 'https://example.com/full2.jpg',
                  displayOrder: 0,
                },
              ],
              confidence_score: 0.90,
            },
          ],
          total: 1,
        }),
      });
    });

    // Expand first meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click delete button
    await page.click('.meal-card:first-child .delete-button');

    // Confirm deletion
    await page.click('.confirmation-dialog .confirm-button');

    // Dialog should close
    await expect(page.locator('.confirmation-dialog')).not.toBeVisible();

    // First meal should be removed from the list
    await expect(page.locator('.meal-card')).toHaveCount(1);
    await expect(page.locator('.meal-card:first-child .meal-description')).toContainText('Breakfast smoothie');
  });

  test('should cancel deletion when cancel button is clicked', async ({ page }) => {
    // Expand first meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click delete button
    await page.click('.meal-card:first-child .delete-button');

    // Cancel deletion
    await page.click('.confirmation-dialog .cancel-button');

    // Dialog should close
    await expect(page.locator('.confirmation-dialog')).not.toBeVisible();

    // Meal should still be in the list
    await expect(page.locator('.meal-card')).toHaveCount(2);
    await expect(page.locator('.meal-card:first-child .meal-description')).toContainText('Chicken pasta dinner');
  });

  test('should show optimistic update before server response', async ({ page }) => {
    // Mock delayed deletion response
    await page.route('**/api/v1/meals/meal-1', async (route) => {
      if (route.request().method() === 'DELETE') {
        // Delay response to test optimistic update
        await new Promise(resolve => setTimeout(resolve, 1000));
        await route.fulfill({
          status: 204,
        });
      } else {
        await route.continue();
      }
    });

    // Expand first meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click delete button
    await page.click('.meal-card:first-child .delete-button');

    // Confirm deletion
    await page.click('.confirmation-dialog .confirm-button');

    // Dialog should close immediately
    await expect(page.locator('.confirmation-dialog')).not.toBeVisible();

    // Meal should be removed immediately (optimistic update)
    await expect(page.locator('.meal-card')).toHaveCount(1);
  });

  test('should revert deletion on server error', async ({ page }) => {
    // Mock failed deletion response
    await page.route('**/api/v1/meals/meal-1', async (route) => {
      if (route.request().method() === 'DELETE') {
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

    // Expand first meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click delete button
    await page.click('.meal-card:first-child .delete-button');

    // Confirm deletion
    await page.click('.confirmation-dialog .confirm-button');

    // Dialog should close
    await expect(page.locator('.confirmation-dialog')).not.toBeVisible();

    // Should show error message
    await expect(page.locator('.error-message')).toContainText('Failed to delete meal');

    // Meal should be restored to the list
    await expect(page.locator('.meal-card')).toHaveCount(2);
    await expect(page.locator('.meal-card:first-child .meal-description')).toContainText('Chicken pasta dinner');
  });

  test('should close dialog when clicking outside', async ({ page }) => {
    // Expand first meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click delete button
    await page.click('.meal-card:first-child .delete-button');

    // Click outside the dialog
    await page.click('.confirmation-dialog', { position: { x: -10, y: -10 } });

    // Dialog should close
    await expect(page.locator('.confirmation-dialog')).not.toBeVisible();

    // Meal should still be in the list
    await expect(page.locator('.meal-card')).toHaveCount(2);
  });

  test('should close dialog when pressing Escape key', async ({ page }) => {
    // Expand first meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click delete button
    await page.click('.meal-card:first-child .delete-button');

    // Press Escape key
    await page.keyboard.press('Escape');

    // Dialog should close
    await expect(page.locator('.confirmation-dialog')).not.toBeVisible();

    // Meal should still be in the list
    await expect(page.locator('.meal-card')).toHaveCount(2);
  });

  test('should be keyboard accessible', async ({ page }) => {
    // Expand first meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Focus delete button and press Enter
    await page.focus('.meal-card:first-child .delete-button');
    await page.keyboard.press('Enter');

    // Confirmation dialog should open
    await expect(page.locator('.confirmation-dialog')).toBeVisible();

    // Tab to confirm button
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Press Enter to confirm
    await page.keyboard.press('Enter');

    // Dialog should close
    await expect(page.locator('.confirmation-dialog')).not.toBeVisible();
  });

  test('should work on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Expand first meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click delete button
    await page.click('.meal-card:first-child .delete-button');

    // Confirmation dialog should be mobile-friendly
    await expect(page.locator('.confirmation-dialog')).toBeVisible();

    // Buttons should be touch-friendly
    const confirmButton = page.locator('.confirmation-dialog .confirm-button');
    const cancelButton = page.locator('.confirmation-dialog .cancel-button');

    const confirmBox = await confirmButton.boundingBox();
    const cancelBox = await cancelButton.boundingBox();

    expect(confirmBox?.height).toBeGreaterThanOrEqual(44);
    expect(cancelBox?.height).toBeGreaterThanOrEqual(44);
  });

  test('should handle deletion of last meal', async ({ page }) => {
    // Mock single meal response
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
                  thumbnailUrl: 'https://example.com/thumb1.jpg',
                  fullUrl: 'https://example.com/full1.jpg',
                  displayOrder: 0,
                },
              ],
              confidence_score: 0.85,
            },
          ],
          total: 1,
        }),
      });
    });

    // Mock successful deletion response
    await page.route('**/api/v1/meals/meal-1', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 204,
        });
      } else {
        await route.continue();
      }
    });

    // Mock empty meals list after deletion
    await page.route('**/api/v1/meals*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          meals: [],
          total: 0,
        }),
      });
    });

    await page.reload();

    // Expand meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click delete button
    await page.click('.meal-card:first-child .delete-button');

    // Confirm deletion
    await page.click('.confirmation-dialog .confirm-button');

    // Should show empty state
    await expect(page.locator('.empty-state')).toBeVisible();
    await expect(page.locator('.empty-state h3')).toContainText('No meals found');
    await expect(page.locator('.empty-state p')).toContainText('No meals recorded for this date');
  });

  test('should update daily summary after deletion', async ({ page }) => {
    // Mock successful deletion response
    await page.route('**/api/v1/meals/meal-1', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 204,
        });
      } else {
        await route.continue();
      }
    });

    // Mock updated daily summary
    await page.route('**/api/v1/daily-summary*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          date: '2025-09-30',
          total_calories: 320.0, // Reduced from 970.0 (650 + 320)
          total_protein: 15.0,   // Reduced from 60.5 (45.5 + 15)
          total_carbs: 45.0,     // Reduced from 120.0 (75 + 45)
          total_fats: 8.0,       // Reduced from 26.2 (18.2 + 8)
          goal_calories: 2000.0,
          goal_protein: 150.0,
          goal_carbs: 250.0,
          goal_fats: 65.0,
        }),
      });
    });

    // Expand first meal card
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click delete button
    await page.click('.meal-card:first-child .delete-button');

    // Confirm deletion
    await page.click('.confirmation-dialog .confirm-button');

    // Daily summary should be updated
    await expect(page.locator('.daily-summary .total-calories')).toContainText('320');
    await expect(page.locator('.daily-summary .total-protein')).toContainText('15.0g');
    await expect(page.locator('.daily-summary .total-carbs')).toContainText('45.0g');
    await expect(page.locator('.daily-summary .total-fats')).toContainText('8.0g');
  });
});
