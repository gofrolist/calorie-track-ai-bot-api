/**
 * E2E Test: Responsive stats graphs
 * Feature: 003-update-logic-for
 * Task: T046
 * Scenario 9: Responsive stats graphs
 */

import { test, expect } from '@playwright/test';

test.describe('Stats Page - Responsive Graphs', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses for stats
    await page.route('**/api/v1/daily-summary*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          date: '2025-09-30',
          total_calories: 1850.0,
          total_protein: 95.5,
          total_carbs: 210.0,
          total_fats: 55.0,
          meal_count: 3,
        }),
      });
    });

    await page.route('**/api/v1/meals/calendar*', async (route) => {
      const url = new URL(route.request().url());
      const startDate = url.searchParams.get('start_date');
      const endDate = url.searchParams.get('end_date');

      if (startDate && endDate) {
        // Generate mock data for the date range
        const dates = [];
        const start = new Date(startDate);
        const end = new Date(endDate);

        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
          dates.push({
            date: d.toISOString().split('T')[0],
            meal_count: Math.floor(Math.random() * 4) + 1,
            total_calories: Math.floor(Math.random() * 1000) + 500,
            total_protein: Math.floor(Math.random() * 50) + 20,
            total_carbs: Math.floor(Math.random() * 100) + 50,
            total_fats: Math.floor(Math.random() * 30) + 10,
          });
        }

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ dates }),
        });
      }
    });

    await page.goto('/stats');
  });

  test('should fit mobile screen width without horizontal scroll', async ({ page }) => {
    // Set mobile viewport (iPhone SE)
    await page.setViewportSize({ width: 375, height: 667 });

    // Check that page loads without horizontal scroll
    const body = page.locator('body');
    const bodyWidth = await body.evaluate((el) => el.scrollWidth);
    const viewportWidth = 375;

    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);

    // Check that charts are visible and fit
    const charts = page.locator('.chart-container');
    await expect(charts.first()).toBeVisible();

    // Check chart width doesn't exceed viewport
    const chartWidth = await charts.first().evaluate((el) => el.scrollWidth);
    expect(chartWidth).toBeLessThanOrEqual(viewportWidth);
  });

  test('should adapt to different mobile screen sizes', async ({ page }) => {
    const viewports = [
      { width: 320, height: 568 }, // iPhone SE
      { width: 375, height: 667 }, // iPhone 8
      { width: 414, height: 896 }, // iPhone 11 Pro Max
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);

      // Charts should be visible and fit
      const charts = page.locator('.chart-container');
      await expect(charts.first()).toBeVisible();

      // No horizontal scroll
      const bodyWidth = await page.locator('body').evaluate((el) => el.scrollWidth);
      expect(bodyWidth).toBeLessThanOrEqual(viewport.width);
    }
  });

  test('should show readable labels on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Check that chart labels are visible and readable
    const chartLabels = page.locator('.chart-container text, .chart-container .tick text');
    await expect(chartLabels.first()).toBeVisible();

    // Check font size is appropriate for mobile
    const fontSize = await chartLabels.first().evaluate((el) => {
      const style = window.getComputedStyle(el);
      return parseFloat(style.fontSize);
    });

    expect(fontSize).toBeGreaterThanOrEqual(10); // Minimum readable size
  });

  test('should maintain aspect ratio on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Check chart aspect ratio
    const chart = page.locator('.chart-container').first();
    const box = await chart.boundingBox();

    if (box) {
      const aspectRatio = box.width / box.height;
      // Should be reasonable aspect ratio (not too wide or too tall)
      expect(aspectRatio).toBeGreaterThan(1.5);
      expect(aspectRatio).toBeLessThan(3.0);
    }
  });

  test('should be touch-friendly on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Check that interactive elements are touch-friendly
    const buttons = page.locator('button, .clickable');
    const buttonCount = await buttons.count();

    for (let i = 0; i < Math.min(buttonCount, 5); i++) {
      const button = buttons.nth(i);
      const box = await button.boundingBox();

      if (box) {
        // Touch targets should be at least 44x44px
        expect(box.height).toBeGreaterThanOrEqual(44);
        expect(box.width).toBeGreaterThanOrEqual(44);
      }
    }
  });

  test('should handle orientation change', async ({ page }) => {
    // Start in portrait
    await page.setViewportSize({ width: 375, height: 667 });

    // Check initial state
    const charts = page.locator('.chart-container');
    await expect(charts.first()).toBeVisible();

    // Rotate to landscape
    await page.setViewportSize({ width: 667, height: 375 });

    // Charts should still be visible and fit
    await expect(charts.first()).toBeVisible();

    // No horizontal scroll in landscape
    const bodyWidth = await page.locator('body').evaluate((el) => el.scrollWidth);
    expect(bodyWidth).toBeLessThanOrEqual(667);
  });

  test('should show weekly and monthly views', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Should have view toggle buttons
    await expect(page.locator('[data-testid="weekly-view"]')).toBeVisible();
    await expect(page.locator('[data-testid="monthly-view"]')).toBeVisible();

    // Click weekly view
    await page.click('[data-testid="weekly-view"]');
    await expect(page.locator('[data-testid="weekly-chart"]')).toBeVisible();

    // Click monthly view
    await page.click('[data-testid="monthly-view"]');
    await expect(page.locator('[data-testid="monthly-chart"]')).toBeVisible();
  });

  test('should handle long data series without overflow', async ({ page }) => {
    // Mock data with many data points (30 days)
    const startDate = new Date('2025-09-01');
    const endDate = new Date('2025-09-30');

    await page.route('**/api/v1/meals/calendar*', async (route) => {
      const dates = [];
      for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        dates.push({
          date: d.toISOString().split('T')[0],
          meal_count: Math.floor(Math.random() * 4) + 1,
          total_calories: Math.floor(Math.random() * 1000) + 500,
          total_protein: Math.floor(Math.random() * 50) + 20,
          total_carbs: Math.floor(Math.random() * 100) + 50,
          total_fats: Math.floor(Math.random() * 30) + 10,
        });
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ dates }),
      });
    });

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Reload to get new data
    await page.reload();

    // Chart should handle 30 data points without horizontal scroll
    const bodyWidth = await page.locator('body').evaluate((el) => el.scrollWidth);
    expect(bodyWidth).toBeLessThanOrEqual(375);

    // Chart should be visible
    await expect(page.locator('.chart-container')).toBeVisible();
  });

  test('should have responsive chart configuration', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Check that chart has responsive configuration
    const chart = page.locator('.chart-container').first();

    // Should have responsive class or data attribute
    const hasResponsiveConfig = await chart.evaluate((el) => {
      return el.classList.contains('responsive') ||
             el.hasAttribute('data-responsive') ||
             el.style.width === '100%';
    });

    expect(hasResponsiveConfig).toBe(true);
  });

  test('should show loading state while fetching data', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Mock slow API response
    await page.route('**/api/v1/meals/calendar*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ dates: [] }),
      });
    });

    // Reload page
    await page.reload();

    // Should show loading state
    await expect(page.locator('[data-testid="loading"]')).toBeVisible();

    // Loading state should fit mobile screen
    const loadingWidth = await page.locator('[data-testid="loading"]').evaluate((el) => el.scrollWidth);
    expect(loadingWidth).toBeLessThanOrEqual(375);
  });

  test('should handle empty data gracefully', async ({ page }) => {
    // Mock empty data
    await page.route('**/api/v1/meals/calendar*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ dates: [] }),
      });
    });

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Reload page
    await page.reload();

    // Should show empty state message
    await expect(page.locator('[data-testid="empty-state"]')).toBeVisible();

    // Empty state should fit mobile screen
    const emptyStateWidth = await page.locator('[data-testid="empty-state"]').evaluate((el) => el.scrollWidth);
    expect(emptyStateWidth).toBeLessThanOrEqual(375);
  });

  test('should maintain performance on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Measure page load time
    const startTime = Date.now();
    await page.goto('/stats');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;

    // Should load within 2 seconds (performance requirement)
    expect(loadTime).toBeLessThan(2000);
  });

  test('should work with different chart types', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Test different chart types if they exist
    const chartTypes = ['bar', 'line', 'area'];

    for (const chartType of chartTypes) {
      const chartElement = page.locator(`[data-chart-type="${chartType}"]`);
      if (await chartElement.count() > 0) {
        await expect(chartElement.first()).toBeVisible();

        // Chart should fit mobile screen
        const chartWidth = await chartElement.first().evaluate((el) => el.scrollWidth);
        expect(chartWidth).toBeLessThanOrEqual(375);
      }
    }
  });
});
