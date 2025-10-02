/**
 * E2E Test: Photo carousel navigation
 * Feature: 003-update-logic-for
 * Task: T045
 * Scenario 6: Instagram-style carousel
 */

import { test, expect } from '@playwright/test';

test.describe('Photo Carousel Navigation', () => {
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
              description: 'Multi-photo meal',
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
                {
                  id: 'photo-3',
                  thumbnail_url: 'https://example.com/thumb3.jpg',
                  full_url: 'https://example.com/full3.jpg',
                  display_order: 2,
                },
              ],
              confidence_score: 0.85,
            },
            {
              id: 'meal-2',
              user_id: 'user-1',
              created_at: '2025-09-30T08:15:00Z',
              description: 'Single photo meal',
              calories: 320.0,
              macronutrients: {
                protein: 15.0,
                carbs: 45.0,
                fats: 8.0,
              },
              photos: [
                {
                  id: 'photo-4',
                  thumbnail_url: 'https://example.com/thumb4.jpg',
                  full_url: 'https://example.com/full4.jpg',
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

  test('should show first photo by default', async ({ page }) => {
    // Expand first meal (has 3 photos)
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Should show photo carousel
    await expect(page.locator('.meal-card:first-child .photo-carousel')).toBeVisible();

    // First photo should be visible
    await expect(page.locator('.meal-card:first-child .meal-photo').first()).toBeVisible();
    await expect(page.locator('.meal-card:first-child .meal-photo').first()).toHaveAttribute('src', 'https://example.com/full1.jpg');
  });

  test('should navigate on swipe left', async ({ page }) => {
    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Swipe left on carousel
    const carousel = page.locator('.meal-card:first-child .meal-photo-swiper');
    await carousel.hover();
    await page.mouse.down();
    await page.mouse.move(-100, 0);
    await page.mouse.up();

    // Should show second photo
    await expect(page.locator('.meal-card:first-child .meal-photo').first()).toHaveAttribute('src', 'https://example.com/full2.jpg');
  });

  test('should navigate on swipe right', async ({ page }) => {
    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Navigate to second photo first
    const carousel = page.locator('.meal-card:first-child .meal-photo-swiper');
    await carousel.hover();
    await page.mouse.down();
    await page.mouse.move(-100, 0);
    await page.mouse.up();

    // Now swipe right to go back
    await carousel.hover();
    await page.mouse.down();
    await page.mouse.move(100, 0);
    await page.mouse.up();

    // Should show first photo again
    await expect(page.locator('.meal-card:first-child .meal-photo').first()).toHaveAttribute('src', 'https://example.com/full1.jpg');
  });

  test('should update active pagination dot on navigation', async ({ page }) => {
    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // First dot should be active
    await expect(page.locator('.meal-card:first-child .swiper-pagination-bullet-active')).toBeVisible();

    // Navigate to second photo
    const carousel = page.locator('.meal-card:first-child .meal-photo-swiper');
    await carousel.hover();
    await page.mouse.down();
    await page.mouse.move(-100, 0);
    await page.mouse.up();

    // Second dot should be active
    await expect(page.locator('.meal-card:first-child .swiper-pagination-bullet').nth(1)).toHaveClass(/swiper-pagination-bullet-active/);
  });

  test('should navigate when pagination dot is clicked', async ({ page }) => {
    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click on third pagination dot
    await page.click('.meal-card:first-child .swiper-pagination-bullet').nth(2);

    // Should show third photo
    await expect(page.locator('.meal-card:first-child .meal-photo').first()).toHaveAttribute('src', 'https://example.com/full3.jpg');
  });

  test('should show navigation arrows on desktop', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1024, height: 768 });

    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Should show navigation arrows
    await expect(page.locator('.meal-card:first-child .swiper-button-next')).toBeVisible();
    await expect(page.locator('.meal-card:first-child .swiper-button-prev')).toBeVisible();
  });

  test('should navigate with arrow buttons', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1024, height: 768 });

    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Click next arrow
    await page.click('.meal-card:first-child .swiper-button-next');

    // Should show second photo
    await expect(page.locator('.meal-card:first-child .meal-photo').first()).toHaveAttribute('src', 'https://example.com/full2.jpg');

    // Click prev arrow
    await page.click('.meal-card:first-child .swiper-button-prev');

    // Should show first photo again
    await expect(page.locator('.meal-card:first-child .meal-photo').first()).toHaveAttribute('src', 'https://example.com/full1.jpg');
  });

  test('should hide controls for single photo', async ({ page }) => {
    // Expand second meal (has 1 photo)
    await page.click('.meal-card:nth-child(2) .meal-thumbnail');

    // Should not show navigation arrows
    await expect(page.locator('.meal-card:nth-child(2) .swiper-button-next')).not.toBeVisible();
    await expect(page.locator('.meal-card:nth-child(2) .swiper-button-prev')).not.toBeVisible();

    // Should not show pagination dots
    await expect(page.locator('.meal-card:nth-child(2) .swiper-pagination')).not.toBeVisible();
  });

  test('should support keyboard navigation', async ({ page }) => {
    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Focus on carousel
    await page.locator('.meal-card:first-child .meal-photo-swiper').focus();

    // Navigate with arrow keys
    await page.keyboard.press('ArrowRight');
    await expect(page.locator('.meal-card:first-child .meal-photo').first()).toHaveAttribute('src', 'https://example.com/full2.jpg');

    await page.keyboard.press('ArrowLeft');
    await expect(page.locator('.meal-card:first-child .meal-photo').first()).toHaveAttribute('src', 'https://example.com/full1.jpg');
  });

  test('should have smooth transitions', async ({ page }) => {
    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Check for CSS transition
    const swiper = page.locator('.meal-card:first-child .meal-photo-swiper');
    const transition = await swiper.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return style.transition;
    });

    expect(transition).toContain('transform');
  });

  test('should sort photos by display order', async ({ page }) => {
    // Mock meal with unsorted photos
    await page.route('**/api/v1/meals*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          meals: [
            {
              id: 'meal-unsorted',
              user_id: 'user-1',
              created_at: '2025-09-30T12:30:00Z',
              description: 'Unsorted photos',
              calories: 500.0,
              macronutrients: {
                protein: 30.0,
                carbs: 50.0,
                fats: 15.0,
              },
              photos: [
                {
                  id: 'photo-3',
                  thumbnail_url: 'https://example.com/thumb3.jpg',
                  full_url: 'https://example.com/full3.jpg',
                  display_order: 2,
                },
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
              confidence_score: 0.80,
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();

    // Expand meal
    await page.click('.meal-card .meal-thumbnail');

    // Photos should be in correct order (0, 1, 2)
    await expect(page.locator('.meal-card .meal-photo').first()).toHaveAttribute('src', 'https://example.com/full1.jpg');

    // Navigate to next photo
    const carousel = page.locator('.meal-card .meal-photo-swiper');
    await carousel.hover();
    await page.mouse.down();
    await page.mouse.move(-100, 0);
    await page.mouse.up();

    await expect(page.locator('.meal-card .meal-photo').first()).toHaveAttribute('src', 'https://example.com/full2.jpg');
  });

  test('should handle touch gestures on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Touch swipe left
    const carousel = page.locator('.meal-card:first-child .meal-photo-swiper');
    await carousel.touchscreen.tap(200, 200);
    await page.touchscreen.tap(200, 200);
    await page.touchscreen.tap(100, 200);

    // Should navigate to next photo
    await expect(page.locator('.meal-card:first-child .meal-photo').first()).toHaveAttribute('src', 'https://example.com/full2.jpg');
  });

  test('should show placeholder for meals without photos', async ({ page }) => {
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
              description: 'No photos',
              calories: 400.0,
              macronutrients: {
                protein: 25.0,
                carbs: 40.0,
                fats: 12.0,
              },
              photos: [],
              confidence_score: 0.75,
            },
          ],
          total: 1,
        }),
      });
    });

    await page.reload();

    // Expand meal
    await page.click('.meal-card .meal-thumbnail');

    // Should show placeholder
    await expect(page.locator('.meal-card .no-photos-placeholder')).toBeVisible();
    await expect(page.locator('.meal-card .no-photos-placeholder')).toContainText('📷 No photos available');
  });

  test('should be accessible with ARIA labels', async ({ page }) => {
    // Expand first meal
    await page.click('.meal-card:first-child .meal-thumbnail');

    // Check for ARIA labels
    const carousel = page.locator('.meal-card:first-child .meal-photo-swiper');
    await expect(carousel).toHaveAttribute('role', 'region');

    // Check for alt text on images
    await expect(page.locator('.meal-card:first-child .meal-photo').first()).toHaveAttribute('alt', 'Multi-photo meal 1');
  });
});
