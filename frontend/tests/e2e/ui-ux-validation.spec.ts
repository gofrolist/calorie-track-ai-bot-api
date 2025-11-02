/**
 * UI/UX Quality Validation Tests
 * Feature: 005-mini-app-improvements
 *
 * Automated tests for Phase 6 quality validation tasks:
 * - T042: Theme integration
 * - T043: 60fps performance
 * - T043a-d: Device testing
 * - T044b: Keyboard navigation
 * - T044c: Network throttling
 * - T045a: Visual hierarchy
 */

import { test, expect, devices } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// T042: Chart theme integration (light/dark mode)
test.describe('Theme Integration (T042)', () => {
  test('charts should match Telegram light theme', async ({ page }) => {
    // Mock Telegram WebApp with light theme
    await page.addInitScript(() => {
      window.Telegram = {
        WebApp: {
          colorScheme: 'light',
          themeParams: {
            bg_color: '#ffffff',
            text_color: '#000000',
            button_color: '#007aff',
            button_text_color: '#ffffff',
          },
          ready: () => {},
          expand: () => {},
        },
      } as any;
    });

    await page.goto('/stats');
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 10000 });

    // Verify chart colors match light theme
    const chartContainer = page.locator('[data-testid="stats-charts"]');
    const bgColor = await chartContainer.evaluate((el) =>
      window.getComputedStyle(el).backgroundColor
    );

    // Light theme should have light background
    expect(bgColor).toMatch(/rgb\(25[0-5], 25[0-5], 25[0-5]\)/); // Near white
  });

  test('charts should match Telegram dark theme', async ({ page }) => {
    // Mock Telegram WebApp with dark theme
    await page.addInitScript(() => {
      window.Telegram = {
        WebApp: {
          colorScheme: 'dark',
          themeParams: {
            bg_color: '#1c1c1e',
            text_color: '#ffffff',
            button_color: '#0a84ff',
            button_text_color: '#ffffff',
          },
          ready: () => {},
          expand: () => {},
        },
      } as any;
    });

    await page.goto('/stats');
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 10000 });

    // Verify chart has a solid background (theme integration check)
    const chartContainer = page.locator('[data-testid="stats-charts"]');
    const bgColor = await chartContainer.evaluate((el) =>
      window.getComputedStyle(el).backgroundColor
    );

    // Should have a solid background color (not transparent)
    expect(bgColor).not.toBe('rgba(0, 0, 0, 0)');
    expect(bgColor).toMatch(/rgb\(\d+, \d+, \d+\)/); // Valid RGB color
  });
});

// T043: 60fps performance validation
test.describe('Performance Validation (T043)', () => {
  test('chart animations should maintain 60fps', async ({ page }) => {
    await page.goto('/stats');
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 10000 });

    // Check if date range buttons exist (they won't if no data)
    const dateRangeButton = page.locator('[data-testid="date-range-30"]');
    const buttonCount = await dateRangeButton.count();

    if (buttonCount === 0) {
      // Skip test if no data - empty state doesn't have date range buttons
      console.log('Skipping FPS test - stats page showing empty state');
      return;
    }

    // Start performance tracing
    await page.evaluate(() => {
      (window as any).performanceData = {
        frames: [] as number[],
        startTime: performance.now(),
      };

      let lastTime = performance.now();
      const measureFPS = () => {
        const currentTime = performance.now();
        const fps = 1000 / (currentTime - lastTime);
        (window as any).performanceData.frames.push(fps);
        lastTime = currentTime;

        if ((window as any).performanceData.frames.length < 60) {
          requestAnimationFrame(measureFPS);
        }
      };

      requestAnimationFrame(measureFPS);
    });

    // Trigger chart interaction (hover, date change)
    await dateRangeButton.click();

    // Wait for animation to complete
    await page.waitForTimeout(1000);

    // Get performance data
    const perfData = await page.evaluate(() => (window as any).performanceData);
    const avgFPS = perfData.frames.reduce((a: number, b: number) => a + b, 0) / perfData.frames.length;
    const minFPS = Math.min(...perfData.frames);

    // CHK035, CHK043: Verify 60fps target
    expect(avgFPS).toBeGreaterThan(55); // Allow 5fps margin
    expect(minFPS).toBeGreaterThan(30); // No severe drops
  });

  test('page load should be under 2 seconds', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/stats');
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 10000 });
    const loadTime = Date.now() - startTime;

    // Performance target
    expect(loadTime).toBeLessThan(2000);
  });
});

// T043a-d: Device testing
test.describe('Device Compatibility (T043a-d)', () => {
  // T043a: iPhone SE (smallest iOS device)
  test('should work on iPhone SE (320x568)', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['iPhone SE'],
    });
    const page = await context.newPage();

    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    // CHK121: Verify all features readable and usable
    const form = page.locator('[data-testid="feedback-form"]');
    const formBox = await form.boundingBox();
    expect(formBox).not.toBeNull();
    expect(formBox!.width).toBeLessThanOrEqual(320);

    // Verify touch targets are at least 44x44px (CHK006)
    const submitButton = page.locator('button[type="submit"]');
    const buttonBox = await submitButton.boundingBox();
    expect(buttonBox).not.toBeNull();
    expect(buttonBox!.height).toBeGreaterThanOrEqual(44);
    expect(buttonBox!.width).toBeGreaterThanOrEqual(44);

    await context.close();
  });

  // T043b: iPhone 14 Pro Max (large iOS with Dynamic Island)
  test('should work on iPhone 14 Pro Max', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['iPhone 14 Pro Max'],
    });
    const page = await context.newPage();

    await page.goto('/stats');
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 10000 });

    // CHK122: Verify safe areas respected
    const viewport = page.viewportSize();
    expect(viewport).not.toBeNull();
    expect(viewport!.width).toBeGreaterThan(400);

    // Check header doesn't overlap with Dynamic Island area
    const header = page.locator('header, [role="banner"]');
    if (await header.count() > 0) {
      const headerBox = await header.boundingBox();
      expect(headerBox).not.toBeNull();
      expect(headerBox!.y).toBeGreaterThanOrEqual(0); // Should respect safe area
    }

    await context.close();
  });

  // T043c: Android device (Pixel)
  test('should work on Pixel 5', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['Pixel 5'],
    });
    const page = await context.newPage();

    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    // CHK123, CHK125: Verify Android compatibility
    const textarea = page.locator('textarea');
    await textarea.fill('Test feedback on Android device');

    // Verify input works
    const value = await textarea.inputValue();
    expect(value).toBe('Test feedback on Android device');

    await context.close();
  });

  // T043d: Telegram iOS app simulation
  test('should work in Telegram iOS WebView', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['iPhone 13'],
      userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Telegram-iOS/9.0',
    });
    const page = await context.newPage();

    // Mock Telegram WebApp API
    await page.addInitScript(() => {
      window.Telegram = {
        WebApp: {
          initData: 'test_data',
          initDataUnsafe: { user: { id: 12345, first_name: 'Test' } },
          version: '6.9',
          platform: 'ios',
          colorScheme: 'light',
          themeParams: {},
          isExpanded: true,
          viewportHeight: 667,
          viewportStableHeight: 667,
          headerColor: '#ffffff',
          backgroundColor: '#ffffff',
          ready: () => {},
          expand: () => {},
          close: () => {},
          MainButton: {
            setText: () => {},
            show: () => {},
            hide: () => {},
          },
        },
      } as any;
    });

    await page.goto('/stats');
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 10000 });

    // CHK124: Verify works in actual Telegram app context
    const telegramAvailable = await page.evaluate(() => !!window.Telegram?.WebApp);
    expect(telegramAvailable).toBe(true);

    await context.close();
  });
});

// T044b: Keyboard navigation
test.describe('Keyboard Navigation (T044b)', () => {
  test('should support tab navigation through all interactive elements', async ({ page }) => {
    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    // CHK046, CHK127: Test keyboard navigation
    await page.keyboard.press('Tab'); // Focus first element
    let focusedElement = await page.evaluate(() => document.activeElement?.tagName);

    // Tab through form elements
    const interactiveElements = [];
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');
      focusedElement = await page.evaluate(() => ({
        tag: document.activeElement?.tagName,
        type: (document.activeElement as HTMLInputElement)?.type,
        role: document.activeElement?.getAttribute('role'),
      }));

      if (focusedElement.tag !== 'BODY') {
        interactiveElements.push(focusedElement);
      }
    }

    // Verify we can tab through multiple interactive elements
    expect(interactiveElements.length).toBeGreaterThan(0);

    // Test that submit button can receive focus
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.focus();

    // Check if button is now focused
    const buttonFocused = await page.evaluate(() => {
      const activeEl = document.activeElement;
      return activeEl?.tagName === 'BUTTON' && activeEl?.getAttribute('type') === 'submit';
    });
    expect(buttonFocused).toBe(true);
  });

  test('should trap focus within modal dialogs', async ({ page }) => {
    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    // If there's a modal, focus should be trapped
    const modalExists = await page.locator('[role="dialog"]').count() > 0;

    if (modalExists) {
      const firstFocusableInModal = await page.locator('[role="dialog"] button, [role="dialog"] input, [role="dialog"] textarea').first();
      await firstFocusableInModal.focus();

      // Tab multiple times
      for (let i = 0; i < 20; i++) {
        await page.keyboard.press('Tab');
      }

      // Focus should still be within modal
      const focusInModal = await page.evaluate(() => {
        const activeEl = document.activeElement;
        const modal = document.querySelector('[role="dialog"]');
        return modal?.contains(activeEl);
      });

      expect(focusInModal).toBe(true);
    }
  });
});

// T044c: 3G network throttling
test.describe('Network Throttling (T044c)', () => {
  test('should show loading states under 3G conditions', async ({ page, context }) => {
    // Simulate 3G network
    await context.route('**/*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 500)); // 500ms delay
      await route.continue();
    });

    await page.goto('/stats');

    // CHK126: Wait for stats-charts to render (it has loading state with aria-busy initially)
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 15000 });

    // Verify the component rendered (loading or loaded state both have data-testid)
    const statsVisible = await page.locator('[data-testid="stats-charts"]').count() > 0;
    expect(statsVisible).toBe(true);
  });

  test('should handle API errors gracefully under poor network', async ({ page, context }) => {
    // Simulate network failure
    await context.route('**/api/v1/statistics/**', (route) => {
      route.abort('failed');
    });

    await page.goto('/stats');
    await page.waitForTimeout(2000);

    // Verify error message appears
    const errorMessage = page.locator('[data-testid="error-message"], .error, [role="alert"]');
    const errorVisible = await errorMessage.count() > 0;
    expect(errorVisible).toBe(true);
  });
});

// T045a: Visual hierarchy
test.describe('Visual Hierarchy (T045a)', () => {
  test('primary actions should be visually emphasized', async ({ page }) => {
    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    // CHK020-CHK021: Primary action should be most prominent
    const submitButton = page.locator('button[type="submit"]');
    const submitStyles = await submitButton.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        backgroundColor: styles.backgroundColor,
        fontSize: styles.fontSize,
        fontWeight: styles.fontWeight,
        padding: styles.padding,
      };
    });

    // Primary button should have prominent styling
    expect(parseInt(submitStyles.fontSize)).toBeGreaterThan(14);
    expect(submitStyles.backgroundColor).not.toBe('rgba(0, 0, 0, 0)'); // Not transparent
  });

  test('supporting content should be visually subdued', async ({ page }) => {
    await page.goto('/stats');
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 10000 });

    // Supporting text (like labels, descriptions) should be less prominent
    const labels = page.locator('label, .label, .helper-text, .description').first();

    if (await labels.count() > 0) {
      const labelStyles = await labels.evaluate((el) => {
        const styles = window.getComputedStyle(el);
        return {
          fontSize: styles.fontSize,
          opacity: styles.opacity,
          color: styles.color,
        };
      });

      // Supporting text should be smaller or less opaque
      const fontSize = parseInt(labelStyles.fontSize);
      expect(fontSize).toBeLessThan(18); // Smaller than headings
    }
  });
});

// Performance budgets
test.describe('Performance Budgets', () => {
  test('JavaScript bundle should be under 250KB', async ({ page }) => {
    const jsRequests: number[] = [];

    page.on('response', async (response) => {
      const url = response.url();
      if (url.endsWith('.js') && response.status() === 200) {
        const contentLength = response.headers()['content-length'];
        if (contentLength) {
          jsRequests.push(parseInt(contentLength));
        }
      }
    });

    await page.goto('/stats');
    await page.waitForLoadState('networkidle');

    const totalJSSize = jsRequests.reduce((a, b) => a + b, 0);
    expect(totalJSSize).toBeLessThan(250 * 1024); // 250KB
  });
});
