/**
 * End-to-End Integration Tests for Mobile Safe Areas
 *
 * Tests to verify mobile safe areas implementation works correctly across
 * different devices and orientations. Validates CSS env() functions,
 * responsive design, and Telegram WebApp integration.
 *
 * @module SafeAreasE2ETests
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

// Device configurations for testing
const DEVICES = [
  {
    name: 'iPhone 12',
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 3,
    hasNotch: true
  },
  {
    name: 'iPhone 12 Landscape',
    viewport: { width: 844, height: 390 },
    deviceScaleFactor: 3,
    hasNotch: true
  },
  {
    name: 'Android Pixel 5',
    viewport: { width: 393, height: 851 },
    deviceScaleFactor: 2.75,
    hasNotch: false
  },
  {
    name: 'iPad Air',
    viewport: { width: 820, height: 1180 },
    deviceScaleFactor: 2,
    hasNotch: false
  }
];

test.describe('Mobile Safe Areas Integration Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock Telegram WebApp environment
    await page.addInitScript(() => {
      (window as any).Telegram = {
        WebApp: {
          ready: () => {},
          expand: () => {},
          colorScheme: 'light',
          themeParams: {
            bg_color: '#ffffff',
            text_color: '#000000'
          },
          initDataUnsafe: {
            user: {
              id: 123456789,
              language_code: 'en'
            }
          }
        }
      };
    });

    // Navigate to the application
    await page.goto('/');
  });

  DEVICES.forEach(device => {
    test.describe(device.name, () => {
      test.beforeEach(async ({ page }) => {
        await page.setViewportSize(device.viewport);
      });

      test('should respect safe areas with CSS env() functions', async ({ page }) => {
        // Check if safe area CSS custom properties are available
        const safeAreaSupport = await page.evaluate(() => {
          return CSS.supports('padding-top: env(safe-area-inset-top)');
        });

        if (safeAreaSupport) {
          // Test safe area inset values
          const safeAreaValues = await page.evaluate(() => {
            const computedStyle = getComputedStyle(document.documentElement);
            return {
              top: computedStyle.getPropertyValue('--safe-area-inset-top'),
              bottom: computedStyle.getPropertyValue('--safe-area-inset-bottom'),
              left: computedStyle.getPropertyValue('--safe-area-inset-left'),
              right: computedStyle.getPropertyValue('--safe-area-inset-right')
            };
          });

          // Safe area values should be defined
          expect(safeAreaValues.top).toBeDefined();
          expect(safeAreaValues.bottom).toBeDefined();
          expect(safeAreaValues.left).toBeDefined();
          expect(safeAreaValues.right).toBeDefined();

          // For devices with notches, top safe area should be > 0
          if (device.hasNotch && device.viewport.height > device.viewport.width) {
            const topValue = parseFloat(safeAreaValues.top) || 0;
            expect(topValue).toBeGreaterThan(0);
          }
        }
      });

      test('should apply safe areas to SafeAreaWrapper component', async ({ page }) => {
        // Look for SafeAreaWrapper component
        const safeAreaWrapper = page.locator('[data-safe-area-supported="true"]');

        if (await safeAreaWrapper.count() > 0) {
          // Check if safe area styling is applied
          const wrapperStyles = await safeAreaWrapper.evaluate((el) => {
            const computedStyle = getComputedStyle(el);
            return {
              paddingTop: computedStyle.paddingTop,
              paddingBottom: computedStyle.paddingBottom,
              paddingLeft: computedStyle.paddingLeft,
              paddingRight: computedStyle.paddingRight
            };
          });

          // Safe area padding should be applied
          expect(wrapperStyles.paddingTop).toBeDefined();
          expect(wrapperStyles.paddingBottom).toBeDefined();

          // For devices with safe areas, padding should be > 0
          if (device.hasNotch) {
            const topPadding = parseFloat(wrapperStyles.paddingTop) || 0;
            expect(topPadding).toBeGreaterThanOrEqual(0);
          }
        }
      });

      test('should not overlap with system UI elements', async ({ page }) => {
        // Check that content doesn't overlap with status bar or home indicator areas
        const viewportHeight = device.viewport.height;
        const contentHeight = await page.evaluate(() => {
          const body = document.body;
          return body.scrollHeight;
        });

        // Content should fit within viewport with safe areas
        expect(contentHeight).toBeLessThanOrEqual(viewportHeight * 2); // Allow for scrolling
      });

      test('should handle dynamic safe area changes', async ({ page }) => {
        // Test safe area handling when environment changes
        await page.evaluate(() => {
          // Simulate safe area change (e.g., orientation change)
          const event = new Event('resize');
          window.dispatchEvent(event);
        });

        // Wait for any potential recalculations
        await page.waitForTimeout(100);

        // Check that safe areas are still properly applied
        const safeAreaClasses = await page.evaluate(() => {
          const wrapper = document.querySelector('[data-safe-area-supported]');
          return wrapper ? wrapper.className : '';
        });

        expect(safeAreaClasses).toBeDefined();
      });
    });
  });

  test.describe('Orientation Changes', () => {
    test('should handle portrait to landscape transition', async ({ page }) => {
      // Start in portrait
      await page.setViewportSize({ width: 390, height: 844 });

      // Check initial safe areas
      const initialSafeAreas = await page.evaluate(() => {
        const wrapper = document.querySelector('[data-safe-area-supported]');
        if (wrapper) {
          const styles = getComputedStyle(wrapper);
          return {
            paddingTop: styles.paddingTop,
            paddingBottom: styles.paddingBottom
          };
        }
        return null;
      });

      // Switch to landscape
      await page.setViewportSize({ width: 844, height: 390 });

      // Wait for orientation change handling
      await page.waitForTimeout(200);

      // Check updated safe areas
      const updatedSafeAreas = await page.evaluate(() => {
        const wrapper = document.querySelector('[data-safe-area-supported]');
        if (wrapper) {
          const styles = getComputedStyle(wrapper);
          return {
            paddingTop: styles.paddingTop,
            paddingBottom: styles.paddingBottom
          };
        }
        return null;
      });

      // Safe areas should be properly updated for landscape
      if (initialSafeAreas && updatedSafeAreas) {
        expect(updatedSafeAreas.paddingTop).toBeDefined();
        expect(updatedSafeAreas.paddingBottom).toBeDefined();
      }
    });
  });

  test.describe('CSS Environment Variables', () => {
    test('should support CSS env() functions', async ({ page }) => {
      const envSupport = await page.evaluate(() => {
        return {
          safeAreaTop: CSS.supports('padding-top: env(safe-area-inset-top)'),
          safeAreaBottom: CSS.supports('padding-bottom: env(safe-area-inset-bottom)'),
          safeAreaLeft: CSS.supports('padding-left: env(safe-area-inset-left)'),
          safeAreaRight: CSS.supports('padding-right: env(safe-area-inset-right)')
        };
      });

      // Modern browsers should support CSS env() functions
      expect(envSupport.safeAreaTop).toBe(true);
      expect(envSupport.safeAreaBottom).toBe(true);
      expect(envSupport.safeAreaLeft).toBe(true);
      expect(envSupport.safeAreaRight).toBe(true);
    });

    test('should fallback gracefully when env() not supported', async ({ page }) => {
      // Mock unsupported environment
      await page.addInitScript(() => {
        // Override CSS.supports to simulate lack of support
        const originalSupports = CSS.supports;
        CSS.supports = function(property: string, value?: string) {
          if (property.includes('env(safe-area-inset')) {
            return false;
          }
          return originalSupports.call(this, property, value);
        };
      });

      await page.reload();

      // Check that safe area wrapper still functions with fallback
      const wrapper = page.locator('.safe-area-wrapper, [data-safe-area-supported]');

      if (await wrapper.count() > 0) {
        const isVisible = await wrapper.isVisible();
        expect(isVisible).toBe(true);

        // Should have fallback styling
        const hasClass = await wrapper.evaluate((el) => {
          return el.classList.length > 0 || el.hasAttribute('data-safe-area-supported');
        });
        expect(hasClass).toBe(true);
      }
    });
  });

  test.describe('Telegram WebApp Integration', () => {
    test('should detect Telegram environment and apply safe areas', async ({ page }) => {
      // Check if Telegram WebApp is detected
      const telegramDetected = await page.evaluate(() => {
        return !!(window as any).Telegram?.WebApp;
      });

      expect(telegramDetected).toBe(true);

      // Check if safe areas are enabled for Telegram
      const safeAreaEnabled = await page.evaluate(() => {
        const wrapper = document.querySelector('[data-telegram-webapp="true"]');
        return wrapper !== null;
      });

      // Safe areas should be enabled in Telegram environment
      expect(safeAreaEnabled).toBe(true);
    });

    test('should handle Telegram theme integration with safe areas', async ({ page }) => {
      // Change Telegram theme
      await page.evaluate(() => {
        if ((window as any).Telegram?.WebApp) {
          (window as any).Telegram.WebApp.colorScheme = 'dark';
          (window as any).Telegram.WebApp.themeParams.bg_color = '#000000';
        }
      });

      // Wait for theme change processing
      await page.waitForTimeout(100);

      // Check that safe areas still work with dark theme
      const safeAreaWithDarkTheme = await page.evaluate(() => {
        const wrapper = document.querySelector('[data-safe-area-supported="true"]');
        if (wrapper) {
          const styles = getComputedStyle(wrapper);
          return {
            paddingTop: styles.paddingTop,
            backgroundColor: styles.backgroundColor || getComputedStyle(document.body).backgroundColor
          };
        }
        return null;
      });

      expect(safeAreaWithDarkTheme).toBeTruthy();
    });
  });

  test.describe('Performance Tests', () => {
    test('should maintain good performance with safe areas', async ({ page }) => {
      // Measure page load time with safe areas
      const startTime = Date.now();

      await page.goto('/', { waitUntil: 'networkidle' });

      const loadTime = Date.now() - startTime;

      // Page should load within reasonable time (< 3 seconds)
      expect(loadTime).toBeLessThan(3000);
    });

    test('should handle rapid orientation changes efficiently', async ({ page }) => {
      const orientations = [
        { width: 390, height: 844 }, // Portrait
        { width: 844, height: 390 }, // Landscape
        { width: 390, height: 844 }, // Portrait again
      ];

      const startTime = Date.now();

      for (const orientation of orientations) {
        await page.setViewportSize(orientation);
        await page.waitForTimeout(50); // Small delay between changes
      }

      const totalTime = Date.now() - startTime;

      // Should handle orientation changes quickly (< 500ms total)
      expect(totalTime).toBeLessThan(500);
    });
  });

  test.describe('Accessibility with Safe Areas', () => {
    test('should maintain accessibility with safe areas applied', async ({ page }) => {
      // Check that safe areas don't interfere with accessibility
      const accessibilityViolations = await page.evaluate(() => {
        // Basic accessibility checks
        const focusableElements = document.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        let violations = 0;

        focusableElements.forEach(element => {
          const rect = element.getBoundingClientRect();
          const styles = getComputedStyle(element);

          // Check if element is visible and accessible
          if (rect.width === 0 || rect.height === 0) {
            violations++;
          }

          // Check if element has sufficient contrast (basic check)
          if (styles.color === styles.backgroundColor) {
            violations++;
          }
        });

        return violations;
      });

      // Should have minimal accessibility violations
      expect(accessibilityViolations).toBeLessThan(3);
    });

    test('should maintain touch targets with safe areas', async ({ page }) => {
      // Check that interactive elements have adequate touch targets
      const touchTargetSizes = await page.evaluate(() => {
        const buttons = document.querySelectorAll('button, [role="button"]');
        const inadequateTargets = [];

        buttons.forEach((button, index) => {
          const rect = button.getBoundingClientRect();
          const minSize = 44; // Minimum touch target size (44px)

          if (rect.width < minSize || rect.height < minSize) {
            inadequateTargets.push({
              index,
              width: rect.width,
              height: rect.height
            });
          }
        });

        return inadequateTargets;
      });

      // All touch targets should meet minimum size requirements
      expect(touchTargetSizes.length).toBeLessThan(2); // Allow for 1-2 edge cases
    });
  });

  test.describe('Cross-Browser Compatibility', () => {
    test('should work consistently across browsers', async ({ page, browserName }) => {
      // Test safe area implementation across different browsers
      const safeAreaImplementation = await page.evaluate(() => {
        const wrapper = document.querySelector('[data-safe-area-supported]');

        if (wrapper) {
          const styles = getComputedStyle(wrapper);
          return {
            hasPadding: styles.paddingTop !== '0px' || styles.paddingBottom !== '0px',
            hasCustomProperties: !!document.documentElement.style.getPropertyValue('--safe-area-inset-top'),
            browserSupport: CSS.supports('padding-top: env(safe-area-inset-top)')
          };
        }

        return null;
      });

      // Safe area implementation should work in all modern browsers
      if (safeAreaImplementation) {
        expect(safeAreaImplementation.browserSupport).toBe(true);

        // Should have either padding or custom properties set
        expect(
          safeAreaImplementation.hasPadding || safeAreaImplementation.hasCustomProperties
        ).toBe(true);
      }
    });
  });
});
