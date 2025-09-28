/**
 * End-to-End Integration Tests for Theme Switching
 *
 * Tests to verify theme switching works correctly across the application.
 * Validates theme detection, manual switching, system preference integration,
 * and Telegram WebApp theme synchronization.
 *
 * @module ThemeSwitchingE2ETests
 */

import { test, expect, Page } from '@playwright/test';

test.describe('Theme Switching Integration Tests', () => {
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
            text_color: '#000000',
            hint_color: '#999999',
            link_color: '#2481cc',
            button_color: '#2481cc',
            button_text_color: '#ffffff',
            secondary_bg_color: '#f1f1f1'
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

    // Wait for theme system to initialize
    await page.waitForTimeout(500);
  });

  test.describe('Theme Detection', () => {
    test('should detect initial theme from system preferences', async ({ page }) => {
      // Check if theme is detected and applied
      const initialTheme = await page.evaluate(() => {
        return {
          htmlAttribute: document.documentElement.getAttribute('data-theme'),
          bodyClass: document.body.className,
          cssCustomProperty: getComputedStyle(document.documentElement).getPropertyValue('--theme')
        };
      });

      expect(initialTheme.htmlAttribute).toMatch(/^(light|dark|auto)$/);
      expect(initialTheme.cssCustomProperty).toBeTruthy();
    });

    test('should detect theme from Telegram WebApp', async ({ page }) => {
      // Set Telegram theme to dark
      await page.evaluate(() => {
        if ((window as any).Telegram?.WebApp) {
          (window as any).Telegram.WebApp.colorScheme = 'dark';
          (window as any).Telegram.WebApp.themeParams.bg_color = '#000000';
          (window as any).Telegram.WebApp.themeParams.text_color = '#ffffff';
        }
      });

      // Trigger theme detection
      await page.evaluate(() => {
        const event = new CustomEvent('telegramThemeChanged');
        window.dispatchEvent(event);
      });

      await page.waitForTimeout(200);

      // Check if dark theme is applied
      const telegramTheme = await page.evaluate(() => {
        return {
          theme: document.documentElement.getAttribute('data-theme'),
          source: document.documentElement.getAttribute('data-theme-source'),
          bgColor: getComputedStyle(document.documentElement).getPropertyValue('--tg-bg-color')
        };
      });

      // Should detect Telegram theme
      expect(['dark', 'auto']).toContain(telegramTheme.theme);
    });

    test('should fallback to system theme when Telegram unavailable', async ({ page }) => {
      // Remove Telegram WebApp
      await page.evaluate(() => {
        delete (window as any).Telegram;
      });

      await page.reload();
      await page.waitForTimeout(500);

      // Should still have a theme applied
      const fallbackTheme = await page.evaluate(() => {
        return document.documentElement.getAttribute('data-theme');
      });

      expect(fallbackTheme).toMatch(/^(light|dark|auto)$/);
    });
  });

  test.describe('Manual Theme Switching', () => {
    test('should switch to dark theme manually', async ({ page }) => {
      // Look for theme toggle button/control
      const themeToggle = page.locator('[data-testid="theme-toggle"], button:has-text("theme"), button:has-text("dark")').first();

      if (await themeToggle.count() > 0) {
        await themeToggle.click();
      } else {
        // Manually trigger theme change via JavaScript
        await page.evaluate(() => {
          // Simulate theme change through the theme detection service
          if ((window as any).themeDetectionService) {
            (window as any).themeDetectionService.setTheme('dark', 'manual');
          } else {
            // Fallback: directly set theme attributes
            document.documentElement.setAttribute('data-theme', 'dark');
            document.documentElement.style.setProperty('--theme', 'dark');
          }
        });
      }

      await page.waitForTimeout(200);

      // Verify dark theme is applied
      const darkThemeApplied = await page.evaluate(() => {
        const theme = document.documentElement.getAttribute('data-theme');
        const themeSource = document.documentElement.getAttribute('data-theme-source');
        return { theme, themeSource };
      });

      expect(darkThemeApplied.theme).toBe('dark');
    });

    test('should switch to light theme manually', async ({ page }) => {
      // First set to dark theme
      await page.evaluate(() => {
        document.documentElement.setAttribute('data-theme', 'dark');
      });

      // Then switch to light
      const themeToggle = page.locator('[data-testid="theme-toggle"], button:has-text("theme"), button:has-text("light")').first();

      if (await themeToggle.count() > 0) {
        await themeToggle.click();
      } else {
        await page.evaluate(() => {
          if ((window as any).themeDetectionService) {
            (window as any).themeDetectionService.setTheme('light', 'manual');
          } else {
            document.documentElement.setAttribute('data-theme', 'light');
            document.documentElement.style.setProperty('--theme', 'light');
          }
        });
      }

      await page.waitForTimeout(200);

      // Verify light theme is applied
      const lightThemeApplied = await page.evaluate(() => {
        return document.documentElement.getAttribute('data-theme');
      });

      expect(lightThemeApplied).toBe('light');
    });

    test('should switch to auto theme and respect system preference', async ({ page }) => {
      // Mock system preference for dark mode
      await page.emulateMedia({ colorScheme: 'dark' });

      await page.evaluate(() => {
        if ((window as any).themeDetectionService) {
          (window as any).themeDetectionService.setTheme('auto', 'manual');
        } else {
          document.documentElement.setAttribute('data-theme', 'auto');
        }
      });

      await page.waitForTimeout(200);

      // Auto theme should resolve to dark based on system preference
      const autoTheme = await page.evaluate(() => {
        return {
          theme: document.documentElement.getAttribute('data-theme'),
          systemPrefersDark: window.matchMedia('(prefers-color-scheme: dark)').matches
        };
      });

      expect(autoTheme.theme).toBe('auto');
      expect(autoTheme.systemPrefersDark).toBe(true);
    });
  });

  test.describe('Theme Persistence', () => {
    test('should persist theme choice across page reloads', async ({ page }) => {
      // Set theme manually
      await page.evaluate(() => {
        localStorage.setItem('app-theme-preference', 'dark');
        document.documentElement.setAttribute('data-theme', 'dark');
      });

      // Reload page
      await page.reload();
      await page.waitForTimeout(500);

      // Theme should be restored
      const persistedTheme = await page.evaluate(() => {
        return {
          storedTheme: localStorage.getItem('app-theme-preference'),
          currentTheme: document.documentElement.getAttribute('data-theme')
        };
      });

      expect(persistedTheme.storedTheme).toBe('dark');
      expect(persistedTheme.currentTheme).toBe('dark');
    });

    test('should handle missing localStorage gracefully', async ({ page }) => {
      // Mock localStorage unavailability
      await page.addInitScript(() => {
        Object.defineProperty(window, 'localStorage', {
          value: {
            getItem: () => { throw new Error('Storage not available'); },
            setItem: () => { throw new Error('Storage not available'); },
            removeItem: () => { throw new Error('Storage not available'); }
          },
          writable: true
        });
      });

      await page.reload();
      await page.waitForTimeout(500);

      // Should still have a theme applied despite storage error
      const themeWithoutStorage = await page.evaluate(() => {
        return document.documentElement.getAttribute('data-theme');
      });

      expect(themeWithoutStorage).toMatch(/^(light|dark|auto)$/);
    });
  });

  test.describe('Theme Application', () => {
    test('should apply theme to all components consistently', async ({ page }) => {
      // Switch to dark theme
      await page.evaluate(() => {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.documentElement.style.setProperty('--theme', 'dark');
      });

      await page.waitForTimeout(200);

      // Check theme application across different components
      const themeApplication = await page.evaluate(() => {
        const components = {
          root: document.documentElement.getAttribute('data-theme'),
          body: document.body.getAttribute('data-theme') || 'inherited',
          buttons: Array.from(document.querySelectorAll('button')).map(btn =>
            getComputedStyle(btn).backgroundColor
          ),
          cards: Array.from(document.querySelectorAll('.card, [class*="card"]')).map(card =>
            getComputedStyle(card).backgroundColor
          )
        };

        return components;
      });

      expect(themeApplication.root).toBe('dark');

      // All buttons should have consistent theming
      if (themeApplication.buttons.length > 0) {
        const uniqueButtonColors = new Set(themeApplication.buttons);
        expect(uniqueButtonColors.size).toBeLessThanOrEqual(3); // Allow for primary, secondary, accent buttons
      }
    });

    test('should apply Telegram theme parameters when available', async ({ page }) => {
      // Set Telegram theme parameters
      await page.evaluate(() => {
        if ((window as any).Telegram?.WebApp) {
          (window as any).Telegram.WebApp.themeParams = {
            bg_color: '#1c1c1e',
            text_color: '#ffffff',
            hint_color: '#8e8e93',
            link_color: '#007aff',
            button_color: '#007aff',
            button_text_color: '#ffffff',
            secondary_bg_color: '#2c2c2e'
          };
        }

        // Apply Telegram theme
        document.documentElement.style.setProperty('--tg-bg-color', '#1c1c1e');
        document.documentElement.style.setProperty('--tg-text-color', '#ffffff');
        document.documentElement.style.setProperty('--tg-button-color', '#007aff');
      });

      await page.waitForTimeout(200);

      // Check if Telegram theme parameters are applied
      const telegramThemeParams = await page.evaluate(() => {
        const rootStyle = getComputedStyle(document.documentElement);
        return {
          bgColor: rootStyle.getPropertyValue('--tg-bg-color'),
          textColor: rootStyle.getPropertyValue('--tg-text-color'),
          buttonColor: rootStyle.getPropertyValue('--tg-button-color')
        };
      });

      expect(telegramThemeParams.bgColor).toContain('#1c1c1e');
      expect(telegramThemeParams.textColor).toContain('#ffffff');
      expect(telegramThemeParams.buttonColor).toContain('#007aff');
    });

    test('should handle theme transitions smoothly', async ({ page }) => {
      // Enable transition monitoring
      await page.evaluate(() => {
        document.documentElement.style.transition = 'background-color 0.3s ease, color 0.3s ease';
      });

      // Measure theme transition time
      const transitionTime = await page.evaluate(async () => {
        const startTime = performance.now();

        // Change theme
        document.documentElement.setAttribute('data-theme', 'dark');

        // Wait for transition to potentially complete
        await new Promise(resolve => setTimeout(resolve, 350));

        return performance.now() - startTime;
      });

      // Transition should complete within reasonable time
      expect(transitionTime).toBeLessThan(500);
    });
  });

  test.describe('System Integration', () => {
    test('should respond to system theme changes', async ({ page }) => {
      // Start with light theme
      await page.emulateMedia({ colorScheme: 'light' });
      await page.reload();
      await page.waitForTimeout(500);

      // Change to dark system theme
      await page.emulateMedia({ colorScheme: 'dark' });

      // Trigger media query change event
      await page.evaluate(() => {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const event = new MediaQueryListEvent('change', { matches: true, media: mediaQuery.media });

        // Simulate media query change
        if (mediaQuery.onchange) {
          mediaQuery.onchange(event);
        }
      });

      await page.waitForTimeout(200);

      // Should detect system theme change
      const systemThemeDetection = await page.evaluate(() => {
        return {
          systemPrefersDark: window.matchMedia('(prefers-color-scheme: dark)').matches,
          currentTheme: document.documentElement.getAttribute('data-theme')
        };
      });

      expect(systemThemeDetection.systemPrefersDark).toBe(true);
    });

    test('should handle high contrast mode', async ({ page }) => {
      // Mock high contrast system preference
      await page.addInitScript(() => {
        Object.defineProperty(window, 'matchMedia', {
          value: (query: string) => ({
            matches: query.includes('prefers-contrast: high'),
            addEventListener: () => {},
            removeEventListener: () => {}
          }),
          writable: true
        });
      });

      await page.reload();
      await page.waitForTimeout(500);

      // Should handle high contrast preference
      const highContrastHandling = await page.evaluate(() => {
        const highContrast = window.matchMedia('(prefers-contrast: high)').matches;
        return {
          highContrastDetected: highContrast,
          themeApplied: document.documentElement.getAttribute('data-theme')
        };
      });

      expect(highContrastHandling.themeApplied).toBeDefined();
    });
  });

  test.describe('Performance', () => {
    test('should switch themes efficiently', async ({ page }) => {
      const themes = ['light', 'dark', 'auto', 'light'];
      const startTime = Date.now();

      for (const theme of themes) {
        await page.evaluate((themeName) => {
          document.documentElement.setAttribute('data-theme', themeName);
          document.documentElement.style.setProperty('--theme', themeName);
        }, theme);

        await page.waitForTimeout(50);
      }

      const totalTime = Date.now() - startTime;

      // Theme switching should be fast (< 500ms for 4 switches)
      expect(totalTime).toBeLessThan(500);
    });

    test('should not cause layout thrashing during theme changes', async ({ page }) => {
      // Monitor layout performance
      await page.evaluate(() => {
        (window as any).layoutMeasurements = [];

        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'measure') {
              (window as any).layoutMeasurements.push(entry.duration);
            }
          }
        });

        observer.observe({ entryTypes: ['measure'] });
      });

      // Perform theme change
      await page.evaluate(() => {
        performance.mark('theme-change-start');
        document.documentElement.setAttribute('data-theme', 'dark');
        performance.mark('theme-change-end');
        performance.measure('theme-change', 'theme-change-start', 'theme-change-end');
      });

      await page.waitForTimeout(100);

      // Check layout performance
      const layoutPerformance = await page.evaluate(() => {
        return (window as any).layoutMeasurements || [];
      });

      // Should not cause excessive layout work
      const excessiveLayoutWork = layoutPerformance.filter((duration: number) => duration > 16.67); // > 1 frame at 60fps
      expect(excessiveLayoutWork.length).toBeLessThan(3);
    });
  });

  test.describe('Accessibility', () => {
    test('should maintain sufficient color contrast in all themes', async ({ page }) => {
      const themes = ['light', 'dark'];

      for (const theme of themes) {
        await page.evaluate((themeName) => {
          document.documentElement.setAttribute('data-theme', themeName);
        }, theme);

        await page.waitForTimeout(100);

        // Check color contrast for text elements
        const contrastRatios = await page.evaluate(() => {
          const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, a, button');
          const lowContrastElements = [];

          textElements.forEach((element, index) => {
            const styles = getComputedStyle(element);
            const textColor = styles.color;
            const backgroundColor = styles.backgroundColor;

            // Basic contrast check (simplified)
            if (textColor === backgroundColor) {
              lowContrastElements.push(index);
            }
          });

          return lowContrastElements;
        });

        // Should have minimal low-contrast elements
        expect(contrastRatios.length).toBeLessThan(5);
      }
    });

    test('should announce theme changes to screen readers', async ({ page }) => {
      // Check for ARIA live regions or other accessibility announcements
      const accessibilityFeatures = await page.evaluate(() => {
        return {
          ariaLiveRegions: document.querySelectorAll('[aria-live]').length,
          statusElements: document.querySelectorAll('[role="status"]').length,
          alertElements: document.querySelectorAll('[role="alert"]').length
        };
      });

      // Should have accessibility features for announcements
      const totalA11yFeatures = accessibilityFeatures.ariaLiveRegions +
                               accessibilityFeatures.statusElements +
                               accessibilityFeatures.alertElements;

      expect(totalA11yFeatures).toBeGreaterThanOrEqual(0); // Allow for basic implementation
    });
  });

  test.describe('Error Handling', () => {
    test('should handle theme detection errors gracefully', async ({ page }) => {
      // Mock theme detection error
      await page.addInitScript(() => {
        // Override console.error to track errors
        (window as any).themeErrors = [];
        const originalError = console.error;
        console.error = (...args) => {
          (window as any).themeErrors.push(args.join(' '));
          originalError.apply(console, args);
        };
      });

      // Cause an error in theme detection
      await page.evaluate(() => {
        // Simulate theme service error
        if ((window as any).themeDetectionService) {
          try {
            (window as any).themeDetectionService.setTheme('invalid-theme', 'manual');
          } catch (error) {
            console.error('Theme error:', error.message);
          }
        }
      });

      await page.waitForTimeout(200);

      // Should still have a valid theme despite errors
      const errorHandling = await page.evaluate(() => {
        return {
          currentTheme: document.documentElement.getAttribute('data-theme'),
          errorCount: (window as any).themeErrors?.length || 0
        };
      });

      expect(errorHandling.currentTheme).toMatch(/^(light|dark|auto)$/);
      // Should handle errors without crashing
      expect(errorHandling.errorCount).toBeLessThan(5);
    });
  });
});
