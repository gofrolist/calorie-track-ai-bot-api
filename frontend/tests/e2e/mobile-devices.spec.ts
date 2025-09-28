/**
 * Mobile Device Testing Validation
 *
 * Comprehensive E2E tests for mobile device compatibility and performance.
 * Tests responsive design, touch interactions, safe areas, and device-specific features.
 */

import { test, expect, devices, Page, BrowserContext } from '@playwright/test';

// Define test device configurations
const mobileDevices = [
  {
    name: 'iPhone 14 Pro',
    device: devices['iPhone 14 Pro'],
    category: 'ios',
    hasNotch: true,
    hasDynamicIsland: true,
    expectedSafeAreaTop: 44,
    expectedSafeAreaBottom: 34,
  },
  {
    name: 'iPhone SE',
    device: devices['iPhone SE'],
    category: 'ios',
    hasNotch: false,
    hasDynamicIsland: false,
    expectedSafeAreaTop: 20,
    expectedSafeAreaBottom: 0,
  },
  {
    name: 'Samsung Galaxy S23',
    device: devices['Galaxy S23'],
    category: 'android',
    hasNotch: false,
    hasDynamicIsland: false,
    expectedSafeAreaTop: 24,
    expectedSafeAreaBottom: 48,
  },
  {
    name: 'iPad Pro',
    device: devices['iPad Pro'],
    category: 'tablet',
    hasNotch: false,
    hasDynamicIsland: false,
    expectedSafeAreaTop: 20,
    expectedSafeAreaBottom: 20,
  },
];

// Performance thresholds
const PERFORMANCE_THRESHOLDS = {
  pageLoadTime: 2000, // 2 seconds
  navigationTime: 1000, // 1 second
  interactionDelay: 300, // 300ms
  animationDuration: 500, // 500ms
};

class DeviceTestHelper {
  constructor(private page: Page) {}

  async measurePageLoadTime(): Promise<number> {
    const startTime = Date.now();
    await this.page.waitForLoadState('domcontentloaded');
    await this.page.waitForLoadState('networkidle');
    return Date.now() - startTime;
  }

  async measureNavigationTime(action: () => Promise<void>): Promise<number> {
    const startTime = Date.now();
    await action();
    await this.page.waitForLoadState('domcontentloaded');
    return Date.now() - startTime;
  }

  async getSafeAreaInsets(): Promise<{ top: number; bottom: number; left: number; right: number }> {
    return await this.page.evaluate(() => {
      const computedStyle = getComputedStyle(document.documentElement);
      return {
        top: parseInt(computedStyle.getPropertyValue('--safe-area-inset-top') || '0'),
        bottom: parseInt(computedStyle.getPropertyValue('--safe-area-inset-bottom') || '0'),
        left: parseInt(computedStyle.getPropertyValue('--safe-area-inset-left') || '0'),
        right: parseInt(computedStyle.getPropertyValue('--safe-area-inset-right') || '0'),
      };
    });
  }

  async checkElementVisibility(selector: string): Promise<boolean> {
    const element = this.page.locator(selector);
    const boundingBox = await element.boundingBox();
    if (!boundingBox) return false;

    const viewport = this.page.viewportSize();
    if (!viewport) return false;

    return (
      boundingBox.x >= 0 &&
      boundingBox.y >= 0 &&
      boundingBox.x + boundingBox.width <= viewport.width &&
      boundingBox.y + boundingBox.height <= viewport.height
    );
  }

  async simulateSwipeGesture(startX: number, startY: number, endX: number, endY: number): Promise<void> {
    await this.page.mouse.move(startX, startY);
    await this.page.mouse.down();
    await this.page.mouse.move(endX, endY);
    await this.page.mouse.up();
  }

  async checkTouchTargetSize(selector: string, minSize: number = 44): Promise<boolean> {
    const element = this.page.locator(selector);
    const boundingBox = await element.boundingBox();
    if (!boundingBox) return false;

    return boundingBox.width >= minSize && boundingBox.height >= minSize;
  }
}

// Run tests for each mobile device
mobileDevices.forEach(({ name, device, category, hasNotch, hasDynamicIsland, expectedSafeAreaTop, expectedSafeAreaBottom }) => {
  test.describe(`Mobile Device Tests - ${name}`, () => {
    test.use({ ...device });

    let helper: DeviceTestHelper;

    test.beforeEach(async ({ page }) => {
      helper = new DeviceTestHelper(page);

      // Set Telegram-specific headers
      await page.setExtraHTTPHeaders({
        'x-telegram-color-scheme': 'light',
        'x-telegram-language-code': 'en',
        'User-Agent': `${device.userAgent} Telegram`,
      });
    });

    test('should load page within performance threshold', async ({ page }) => {
      const loadTime = await helper.measurePageLoadTime();
      await page.goto('/');

      expect(loadTime).toBeLessThan(PERFORMANCE_THRESHOLDS.pageLoadTime);

      // Verify page content is visible
      await expect(page.locator('body')).toBeVisible();
      await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
    });

    test('should apply correct safe area insets', async ({ page }) => {
      await page.goto('/');

      // Wait for safe area detection
      await page.waitForTimeout(1000);

      const safeAreas = await helper.getSafeAreaInsets();

      // Verify safe areas are detected correctly for device type
      if (hasNotch || hasDynamicIsland) {
        expect(safeAreas.top).toBeGreaterThanOrEqual(expectedSafeAreaTop - 5); // Allow 5px tolerance
        expect(safeAreas.top).toBeLessThanOrEqual(expectedSafeAreaTop + 5);
      }

      if (category === 'android' || hasNotch) {
        expect(safeAreas.bottom).toBeGreaterThanOrEqual(expectedSafeAreaBottom - 5);
        expect(safeAreas.bottom).toBeLessThanOrEqual(expectedSafeAreaBottom + 5);
      }

      // Verify safe areas are applied to wrapper
      const wrapper = page.locator('.safe-area-wrapper');
      const wrapperStyle = await wrapper.evaluate(el => getComputedStyle(el));

      expect(parseInt(wrapperStyle.paddingTop)).toBe(safeAreas.top);
      expect(parseInt(wrapperStyle.paddingBottom)).toBe(safeAreas.bottom);
    });

    test('should handle orientation changes correctly', async ({ page }) => {
      await page.goto('/');

      // Test portrait orientation
      const portraitViewport = device.viewport;
      await page.setViewportSize(portraitViewport);
      await page.waitForTimeout(500);

      const portraitSafeAreas = await helper.getSafeAreaInsets();

      // Test landscape orientation
      const landscapeViewport = {
        width: portraitViewport.height,
        height: portraitViewport.width,
      };
      await page.setViewportSize(landscapeViewport);
      await page.waitForTimeout(500);

      const landscapeSafeAreas = await helper.getSafeAreaInsets();

      // Verify safe areas change appropriately for landscape
      if (hasNotch || hasDynamicIsland) {
        // In landscape, notch affects side safe areas
        expect(landscapeSafeAreas.left + landscapeSafeAreas.right).toBeGreaterThan(0);
      }

      // Verify content remains accessible
      await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
    });

    test('should have accessible touch targets', async ({ page }) => {
      await page.goto('/');

      // Check common interactive elements
      const interactiveSelectors = [
        'button',
        'a',
        '[role="button"]',
        'input',
        '[data-testid="nav-item"]',
      ];

      for (const selector of interactiveSelectors) {
        const elements = page.locator(selector);
        const count = await elements.count();

        for (let i = 0; i < count; i++) {
          const element = elements.nth(i);
          if (await element.isVisible()) {
            const hasValidTouchTarget = await helper.checkTouchTargetSize(selector);
            expect(hasValidTouchTarget).toBe(true);
          }
        }
      }
    });

    test('should support touch gestures', async ({ page }) => {
      await page.goto('/');

      const viewport = page.viewportSize()!;

      // Test vertical swipe gesture
      await helper.simulateSwipeGesture(
        viewport.width / 2,
        viewport.height * 0.8,
        viewport.width / 2,
        viewport.height * 0.2
      );

      // Verify page responded to gesture (scroll or navigation)
      await page.waitForTimeout(500);

      // Test horizontal swipe gesture (if applicable)
      await helper.simulateSwipeGesture(
        viewport.width * 0.8,
        viewport.height / 2,
        viewport.width * 0.2,
        viewport.height / 2
      );

      await page.waitForTimeout(500);

      // Verify app is still responsive
      await expect(page.locator('body')).toBeVisible();
    });

    test('should display theme correctly', async ({ page }) => {
      await page.goto('/');

      // Wait for theme detection
      await page.waitForTimeout(1000);

      // Verify theme is applied
      const bodyClasses = await page.locator('body').getAttribute('class');
      const htmlDataTheme = await page.locator('html').getAttribute('data-theme');

      expect(htmlDataTheme).toMatch(/light|dark|auto/);

      // Verify Telegram theme colors are applied
      const rootStyles = await page.evaluate(() => {
        const styles = getComputedStyle(document.documentElement);
        return {
          bgColor: styles.getPropertyValue('--tg-bg-color'),
          textColor: styles.getPropertyValue('--tg-text-color'),
        };
      });

      expect(rootStyles.bgColor).toBeTruthy();
      expect(rootStyles.textColor).toBeTruthy();
    });

    test('should handle navigation performance', async ({ page }) => {
      await page.goto('/');

      // Test navigation to different pages
      const pages = ['/stats', '/goals', '/'];

      for (const pagePath of pages) {
        const navigationTime = await helper.measureNavigationTime(async () => {
          if (pagePath === '/') {
            await page.locator('[data-testid="nav-today"]').click();
          } else if (pagePath === '/stats') {
            await page.locator('[data-testid="nav-stats"]').click();
          } else if (pagePath === '/goals') {
            await page.locator('[data-testid="nav-goals"]').click();
          }
        });

        expect(navigationTime).toBeLessThan(PERFORMANCE_THRESHOLDS.navigationTime);

        // Verify page content loaded
        await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
        await page.waitForTimeout(100); // Brief pause between navigations
      }
    });

    test('should handle text input correctly', async ({ page }) => {
      await page.goto('/');

      // Find text input elements
      const inputs = page.locator('input[type="text"], input[type="number"], textarea');
      const inputCount = await inputs.count();

      if (inputCount > 0) {
        const firstInput = inputs.first();

        // Test focus
        await firstInput.focus();
        await expect(firstInput).toBeFocused();

        // Test text input
        await firstInput.fill('Test input');
        await expect(firstInput).toHaveValue('Test input');

        // Verify keyboard doesn't break layout
        const safeAreasAfterKeyboard = await helper.getSafeAreaInsets();
        expect(safeAreasAfterKeyboard.bottom).toBeGreaterThanOrEqual(0);

        // Clear input
        await firstInput.clear();
        await expect(firstInput).toHaveValue('');
      }
    });

    test('should maintain performance during interactions', async ({ page }) => {
      await page.goto('/');

      // Simulate rapid interactions
      const interactionElements = page.locator('button, a, [role="button"]');
      const elementCount = Math.min(await interactionElements.count(), 5);

      for (let i = 0; i < elementCount; i++) {
        const element = interactionElements.nth(i);

        if (await element.isVisible()) {
          const startTime = Date.now();
          await element.click();
          const interactionTime = Date.now() - startTime;

          expect(interactionTime).toBeLessThan(PERFORMANCE_THRESHOLDS.interactionDelay);

          // Wait for any animations to complete
          await page.waitForTimeout(100);
        }
      }

      // Verify app is still responsive
      await expect(page.locator('body')).toBeVisible();
    });

    test('should handle error states gracefully', async ({ page }) => {
      // Test with network errors
      await page.route('**/api/**', route => route.abort());

      await page.goto('/');

      // Verify error handling doesn't break layout
      const safeAreas = await helper.getSafeAreaInsets();
      expect(safeAreas.top).toBeGreaterThanOrEqual(0);
      expect(safeAreas.bottom).toBeGreaterThanOrEqual(0);

      // Verify error message is shown within safe areas
      const errorElement = page.locator('[data-testid="error-message"]');
      if (await errorElement.isVisible()) {
        const isWithinSafeArea = await helper.checkElementVisibility('[data-testid="error-message"]');
        expect(isWithinSafeArea).toBe(true);
      }
    });

    if (category === 'ios') {
      test('should handle iOS-specific features', async ({ page }) => {
        await page.goto('/');

        // Test iOS momentum scrolling
        await page.evaluate(() => {
          document.documentElement.style.webkitOverflowScrolling = 'touch';
        });

        // Test status bar style
        const metaTags = await page.locator('meta[name="apple-mobile-web-app-status-bar-style"]');
        if (await metaTags.count() > 0) {
          const content = await metaTags.getAttribute('content');
          expect(content).toMatch(/default|black|black-translucent/);
        }

        // Verify safe areas work with iOS features
        if (hasNotch || hasDynamicIsland) {
          const safeAreas = await helper.getSafeAreaInsets();
          expect(safeAreas.top).toBeGreaterThan(20); // Should account for notch/island
        }
      });
    }

    if (category === 'android') {
      test('should handle Android-specific features', async ({ page }) => {
        await page.goto('/');

        // Test Android navigation gestures
        const viewport = page.viewportSize()!;

        // Simulate back gesture
        await helper.simulateSwipeGesture(
          0,
          viewport.height / 2,
          viewport.width * 0.3,
          viewport.height / 2
        );

        await page.waitForTimeout(500);

        // Verify app handles the gesture gracefully
        await expect(page.locator('body')).toBeVisible();

        // Test system bars handling
        const safeAreas = await helper.getSafeAreaInsets();
        expect(safeAreas.bottom).toBeGreaterThanOrEqual(0); // Should account for nav bar
      });
    }

    if (category === 'tablet') {
      test('should adapt to tablet layout', async ({ page }) => {
        await page.goto('/');

        // Verify responsive design for tablets
        const viewport = page.viewportSize()!;
        expect(viewport.width).toBeGreaterThan(768);

        // Check if layout adapts to larger screen
        const mainContent = page.locator('[data-testid="main-content"]');
        const boundingBox = await mainContent.boundingBox();

        if (boundingBox) {
          // Content should use available space efficiently
          expect(boundingBox.width).toBeGreaterThan(400);
          expect(boundingBox.width).toBeLessThan(viewport.width * 0.9);
        }

        // Verify touch targets are still appropriately sized
        const buttons = page.locator('button');
        const buttonCount = Math.min(await buttons.count(), 3);

        for (let i = 0; i < buttonCount; i++) {
          const hasValidTouchTarget = await helper.checkTouchTargetSize('button');
          expect(hasValidTouchTarget).toBe(true);
        }
      });
    }
  });
});

// Cross-device compatibility tests
test.describe('Cross-Device Compatibility', () => {
  test('should maintain consistent behavior across devices', async ({ browser }) => {
    const results: any[] = [];

    // Test same functionality on different devices
    for (const { name, device } of mobileDevices) {
      const context = await browser.newContext({ ...device });
      const page = await context.newPage();

      await page.setExtraHTTPHeaders({
        'x-telegram-color-scheme': 'light',
        'x-telegram-language-code': 'en',
      });

      const helper = new DeviceTestHelper(page);
      const loadTime = await helper.measurePageLoadTime();
      await page.goto('/');

      results.push({
        device: name,
        loadTime,
        viewport: device.viewport,
      });

      await context.close();
    }

    // Verify consistent performance across devices
    const loadTimes = results.map(r => r.loadTime);
    const avgLoadTime = loadTimes.reduce((a, b) => a + b, 0) / loadTimes.length;
    const maxLoadTime = Math.max(...loadTimes);

    expect(maxLoadTime).toBeLessThan(PERFORMANCE_THRESHOLDS.pageLoadTime);
    expect(maxLoadTime - Math.min(...loadTimes)).toBeLessThan(1000); // Max 1s variance
  });
});

// Performance monitoring test
test.describe('Mobile Performance Monitoring', () => {
  test('should track performance metrics', async ({ page }) => {
    await page.goto('/');

    // Measure performance metrics
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
      };
    });

    // Verify performance metrics meet mobile requirements
    expect(performanceMetrics.domContentLoaded).toBeLessThan(1500); // 1.5s for DOM
    expect(performanceMetrics.firstContentfulPaint).toBeLessThan(2000); // 2s for FCP

    console.log('Performance Metrics:', performanceMetrics);
  });
});
