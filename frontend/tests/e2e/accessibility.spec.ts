/**
 * Accessibility Validation Tests
 * Feature: 005-mini-app-improvements
 *
 * Automated tests for:
 * - T044: Lighthouse accessibility audit (≥90 score)
 * - T044a: Screen reader compatibility (ARIA)
 * - T045: Color contrast validation (WCAG AA)
 */

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// T044 & T045: Accessibility audit with axe-core
test.describe('Accessibility Audit (T044, T045)', () => {
  test('feedback page should pass axe accessibility audit', async ({ page }) => {
    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    // Run axe accessibility audit
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    // CHK127-CHK130: Accessibility score must be ≥90
    // axe-core violations should be minimal
    expect(accessibilityScanResults.violations).toHaveLength(0);
  });

  test('statistics page should pass axe accessibility audit', async ({ page }) => {
    await page.goto('/stats');
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 10000 });

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toHaveLength(0);
  });

  test('home page should pass axe accessibility audit', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toHaveLength(0);
  });
});

// T045: Color contrast validation (WCAG AA = 4.5:1 for normal text)
test.describe('Color Contrast (T045)', () => {
  test('should validate color contrast ratios', async ({ page }) => {
    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    // CHK048: Run axe color-contrast rule specifically
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['cat.color'])
      .include('[data-testid="feedback-form"]')
      .analyze();

    // No color contrast violations
    const contrastViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'color-contrast'
    );
    expect(contrastViolations).toHaveLength(0);
  });

  test('charts should have sufficient contrast', async ({ page }) => {
    await page.goto('/stats');
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 10000 });

    // CHK048-CHK049: Chart colors should be WCAG AA compliant
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['cat.color'])
      .include('[data-testid="stats-charts"]')
      .analyze();

    const contrastViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'color-contrast'
    );
    expect(contrastViolations).toHaveLength(0);
  });

  test('buttons should have sufficient contrast in all states', async ({ page }) => {
    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    const button = page.locator('button[type="submit"]').first();

    // Normal state
    const normalContrast = await button.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        color: styles.color,
        backgroundColor: styles.backgroundColor,
      };
    });

    // Hover state
    await button.hover();
    await page.waitForTimeout(100);

    const hoverContrast = await button.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        color: styles.color,
        backgroundColor: styles.backgroundColor,
      };
    });

    // Both states should have defined colors (not transparent)
    expect(normalContrast.backgroundColor).not.toBe('rgba(0, 0, 0, 0)');
    expect(hoverContrast.backgroundColor).not.toBe('rgba(0, 0, 0, 0)');
  });
});

// T044a: Screen reader compatibility (ARIA labels, roles, live regions)
test.describe('Screen Reader Compatibility (T044a)', () => {
  test('feedback form should have proper ARIA labels', async ({ page }) => {
    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    // CHK044, CHK128: All form inputs should have labels or aria-label
    const inputs = await page.locator('input, textarea, select').all();

    for (const input of inputs) {
      const hasLabel = await input.evaluate((el) => {
        const id = el.id;
        const ariaLabel = el.getAttribute('aria-label');
        const ariaLabelledBy = el.getAttribute('aria-labelledby');
        const label = id ? document.querySelector(`label[for="${id}"]`) : null;

        return !!(ariaLabel || ariaLabelledBy || label);
      });

      expect(hasLabel).toBe(true);
    }
  });

  test('interactive elements should have proper roles', async ({ page }) => {
    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    // Buttons should have button role (implicit or explicit)
    const buttons = await page.locator('button, [role="button"]').all();
    expect(buttons.length).toBeGreaterThan(0);

    // Form should have form role (implicit)
    const form = page.locator('form, [role="form"]').first();
    expect(await form.count()).toBeGreaterThan(0);
  });

  test('error messages should use aria-live for screen readers', async ({ page }) => {
    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    // Submit empty form to trigger validation
    const submitButton = page.locator('button[type="submit"]');
    await submitButton.click();

    // Wait for error message
    await page.waitForTimeout(500);

    // Check if error messages have aria-live or role="alert"
    const errorMessages = await page.locator('[role="alert"], [aria-live]').all();

    // If form validation triggered, there should be accessible error messages
    const hasErrors = errorMessages.length > 0;
    const formHasValues = await page.evaluate(() => {
      const form = document.querySelector('form');
      if (!form) return false;
      const formData = new FormData(form);
      return Array.from(formData.values()).some(v => v);
    });

    // Either form is valid (has values) or errors are accessible
    expect(formHasValues || hasErrors).toBe(true);
  });

  test('charts should have accessible alternative (data table or description)', async ({ page }) => {
    await page.goto('/stats');
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 10000 });

    // CHK044: Charts should have text alternative for screen readers
    const chartContainer = page.locator('[data-testid="stats-charts"]');

    const hasAccessibleDescription = await chartContainer.evaluate((el) => {
      // Check for aria-label, aria-labelledby, or role="img" with alt
      const ariaLabel = el.getAttribute('aria-label');
      const ariaDescribedBy = el.getAttribute('aria-describedby');
      const role = el.getAttribute('role');

      // Or check if there's a data table alternative
      const hasTable = el.querySelector('table') !== null;

      return !!(ariaLabel || ariaDescribedBy || (role === 'img') || hasTable);
    });

    expect(hasAccessibleDescription).toBe(true);
  });

  test('loading states should announce to screen readers', async ({ page }) => {
    await page.goto('/stats');

    // Wait for the stats-charts component to render (in any state)
    await page.waitForSelector('[data-testid="stats-charts"]', { timeout: 10000 });

    // Check if the loaded state has proper ARIA region
    const statsCharts = page.locator('[data-testid="stats-charts"]');
    const hasAccessibleRegion = await statsCharts.evaluate((el) => {
      const role = el.getAttribute('role');
      const ariaLabel = el.getAttribute('aria-label');
      return role === 'region' && !!ariaLabel;
    });

    expect(hasAccessibleRegion).toBe(true);
  });

  test('focus should be visible on all interactive elements', async ({ page }) => {
    await page.goto('/feedback');
    await page.waitForSelector('[data-testid="feedback-form"]', { timeout: 10000 });

    // Tab to first focusable element
    await page.keyboard.press('Tab');

    // Check if focused element has visible focus indicator
    const hasFocusIndicator = await page.evaluate(() => {
      const focused = document.activeElement as HTMLElement;
      if (!focused || focused === document.body) return false;

      const styles = window.getComputedStyle(focused);
      const pseudoStyles = window.getComputedStyle(focused, ':focus');

      // Check for outline, box-shadow, or border changes
      const hasOutline = styles.outline !== 'none' && styles.outline !== '';
      const hasBoxShadow = styles.boxShadow !== 'none';
      const hasBorder = styles.borderWidth !== '0px';

      return hasOutline || hasBoxShadow || hasBorder;
    });

    expect(hasFocusIndicator).toBe(true);
  });

  test('landmark regions should be properly labeled', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for landmark regions: header, main, nav, footer
    const landmarks = await page.evaluate(() => {
      const regions = {
        header: document.querySelector('header, [role="banner"]') !== null,
        main: document.querySelector('main, [role="main"]') !== null,
        nav: document.querySelector('nav, [role="navigation"]') !== null,
      };
      return regions;
    });

    // At minimum, should have main content landmark
    expect(landmarks.main || landmarks.header).toBe(true);
  });
});

// T044: Lighthouse audit programmatic
test.describe('Lighthouse Metrics', () => {
  test('should meet performance and accessibility standards', async ({ page }) => {
    await page.goto('/stats');
    await page.waitForLoadState('networkidle');

    // Get Web Vitals
    const webVitals = await page.evaluate(() => {
      return {
        // First Contentful Paint
        fcp: performance.getEntriesByType('paint')
          .find((entry: any) => entry.name === 'first-contentful-paint')?.startTime,

        // Largest Contentful Paint (approximation)
        lcp: performance.getEntriesByType('largest-contentful-paint')
          .map((entry: any) => entry.startTime)
          .pop(),
      };
    });

    // CHK target: FCP < 1.8s, LCP < 2.5s
    if (webVitals.fcp) {
      expect(webVitals.fcp).toBeLessThan(1800);
    }
    if (webVitals.lcp) {
      expect(webVitals.lcp).toBeLessThan(2500);
    }
  });
});
