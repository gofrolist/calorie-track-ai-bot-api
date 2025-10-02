/**
 * E2E Test: Inline meal card expansion
 * Feature: 003-update-logic-for
 * Task: T044
 * Scenario 5: Inline meal card expansion
 */

import { test, expect } from '@playwright/test';

test.describe('Meal Card Expansion', () => {
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
                {
                  id: 'photo-2',
                  thumbnail_url: 'https://example.com/thumb2.jpg',
                  full_url: 'https://example.com/full2.jpg',
                  display_order: 1,
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
                  id: 'photo-3',
                  thumbnail_url: 'https://example.com/thumb3.jpg',
                  full_url: 'https://example.com/full3.jpg',
                  display_order: 0,
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

  test('should expand meal card on thumbnail click', async ({ page }) => {
    // Initially, meal cards should be collapsed
    await expect(page.locator('.meal-card.expanded')).toHaveCount(0);

    // Click on first meal thumbnail
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Card should expand
    await expect(page.locator('.meal-card:first-child.expanded')).toBeVisible();

    // Should show expanded content
    await expect(page.locator('.meal-card:first-child .meal-card-details')).toBeVisible();
    await expect(page.locator('.meal-card:first-child .macronutrients')).toBeVisible();
    await expect(page.locator('.meal-card:first-child .meal-actions')).toBeVisible();
  });

  test('should show photo carousel for multi-photo meals', async ({ page }) => {
    // Expand first meal (has 2 photos)
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Should show photo carousel
    await expect(page.locator('.meal-card:first-child .photo-carousel')).toBeVisible();

    // Should show navigation controls for multiple photos
    await expect(page.locator('.meal-card:first-child .swiper-navigation')).toBeVisible();
    await expect(page.locator('.meal-card:first-child .swiper-pagination')).toBeVisible();
  });

  test('should hide carousel controls for single-photo meals', async ({ page }) => {
    // Expand second meal (has 1 photo)
    await page.click('.meal-card:nth-child(2) .meal-thumbnail');

    // Should show photo carousel
    await expect(page.locator('.meal-card:nth-child(2) .photo-carousel')).toBeVisible();

    // Should not show navigation controls for single photo
    await expect(page.locator('.meal-card:nth-child(2) .swiper-navigation')).not.toBeVisible();
    await expect(page.locator('.meal-card:nth-child(2) .swiper-pagination')).not.toBeVisible();
  });

  test('should display macronutrients in grams', async ({ page }) => {
    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Should show macronutrients section
    await expect(page.locator('.meal-card:first-child .macronutrients h4')).toContainText('🏋️ Macronutrients');

    // Should show protein, carbs, fats in grams
    await expect(page.locator('.meal-card:first-child .macro-item').nth(0)).toContainText('Protein');
    await expect(page.locator('.meal-card:first-child .macro-item').nth(0)).toContainText('45.5g');

    await expect(page.locator('.meal-card:first-child .macro-item').nth(1)).toContainText('Carbs');
    await expect(page.locator('.meal-card:first-child .macro-item').nth(1)).toContainText('75.0g');

    await expect(page.locator('.meal-card:first-child .macro-item').nth(2)).toContainText('Fats');
    await expect(page.locator('.meal-card:first-child .macro-item').nth(2)).toContainText('18.2g');
  });

  test('should show edit and delete buttons when expanded', async ({ page }) => {
    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Should show action buttons
    await expect(page.locator('.meal-card:first-child .edit-button')).toBeVisible();
    await expect(page.locator('.meal-card:first-child .delete-button')).toBeVisible();

    await expect(page.locator('.meal-card:first-child .edit-button')).toContainText('✏️ Edit');
    await expect(page.locator('.meal-card:first-child .delete-button')).toContainText('🗑️ Delete');
  });

  test('should collapse previous card when expanding new one', async ({ page }) => {
    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');
    await expect(page.locator('.meal-card:first-child.expanded')).toBeVisible();

    // Expand second meal
    await page.click('.meal-card:nth-child(2) .meal-thumbnail');

    // First meal should collapse, second should expand
    await expect(page.locator('.meal-card:first-child.expanded')).not.toBeVisible();
    await expect(page.locator('.meal-card:nth-child(2).expanded')).toBeVisible();
  });

  test('should collapse card when clicking same thumbnail again', async ({ page }) => {
    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');
    await expect(page.locator('.meal-card:first-child.expanded')).toBeVisible();

    // Click same thumbnail again
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Card should collapse
    await expect(page.locator('.meal-card:first-child.expanded')).not.toBeVisible();
  });

  test('should show expand/collapse indicator', async ({ page }) => {
    // Initially should show expand indicator
    await expect(page.locator('.meal-card:first-child .expand-indicator')).toContainText('▶');

    // Expand meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Should show collapse indicator
    await expect(page.locator('.meal-card:first-child .expand-indicator')).toContainText('▼');

    // Collapse meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Should show expand indicator again
    await expect(page.locator('.meal-card:first-child .expand-indicator')).toContainText('▶');
  });

  test('should show photo count badge for multi-photo meals', async ({ page }) => {
    // First meal has 2 photos, should show badge
    await expect(page.locator('.meal-card:first-child .photo-count-badge')).toContainText('2');

    // Second meal has 1 photo, should not show badge
    await expect(page.locator('.meal-card:nth-child(2) .photo-count-badge')).not.toBeVisible();
  });

  test('should preserve scroll position on expand/collapse', async ({ page }) => {
    // Scroll down a bit
    await page.evaluate(() => window.scrollTo(0, 100));

    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Check scroll position is preserved
    const scrollY = await page.evaluate(() => window.scrollY);
    expect(scrollY).toBe(100);

    // Collapse meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Scroll position should still be preserved
    const scrollYAfter = await page.evaluate(() => window.scrollY);
    expect(scrollYAfter).toBe(100);
  });

  test('should have smooth animation on expand/collapse', async ({ page }) => {
    // Check for CSS animation
    const mealCard = page.locator('.meal-card:first-child');
    const animation = await mealCard.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return style.transition;
    });

    expect(animation).toContain('all 0.3s ease');
  });

  test('should handle meals without photos', async ({ page }) => {
    // Mock meal without photos
    await page.route('**/api/v1/meals*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          meals: [
            {
              id: 'meal-no-photos',
              user_id: 'user-1',
              created_at: '2025-09-30T12:30:00Z',
              description: 'Meal without photos',
              calories: 500.0,
              macronutrients: {
                protein: 30.0,
                carbs: 50.0,
                fats: 15.0,
              },
              photos: [],
              confidence_score: 0.80,
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();

    // Should show placeholder icon
    await expect(page.locator('.meal-card .placeholder-icon')).toContainText('🍎');

    // Should not show photo count badge
    await expect(page.locator('.meal-card .photo-count-badge')).not.toBeVisible();

    // Expand meal
    await page.click('.meal-card .meal-thumbnail');

    // Should not show photo carousel
    await expect(page.locator('.meal-card .photo-carousel')).not.toBeVisible();
  });

  test('should be touch-friendly on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Touch targets should be at least 44px
    const thumbnail = page.locator('.meal-card:first-child .meal-thumbnail');
    const box = await thumbnail.boundingBox();
    expect(box?.height).toBeGreaterThanOrEqual(44);
    expect(box?.width).toBeGreaterThanOrEqual(44);

    // Should work with touch
    await thumbnail.tap();
    await expect(page.locator('.meal-card:first-child.expanded')).toBeVisible();
  });
});
