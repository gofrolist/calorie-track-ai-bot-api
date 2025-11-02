# UI/UX Automated Testing Guide

## Overview

This document describes the automated UI/UX validation tests for the 005-mini-app-improvements feature. All manual testing tasks from Phase 6 have been converted to automated Playwright tests with axe-core accessibility validation.

## Test Files

### 1. `tests/e2e/ui-ux-validation.spec.ts`
Covers functional UI/UX requirements:
- **T042**: Theme integration (light/dark mode)
- **T043**: 60fps performance validation
- **T043a-d**: Device compatibility (iPhone SE, Pro Max, Android, Telegram WebView)
- **T044b**: Keyboard navigation
- **T044c**: Network throttling
- **T045a**: Visual hierarchy

### 2. `tests/e2e/accessibility.spec.ts`
Covers accessibility (WCAG AA) requirements:
- **T044**: Accessibility audit with axe-core
- **T044a**: Screen reader compatibility (ARIA labels, roles)
- **T045**: Color contrast validation (4.5:1 ratio)

## Running Tests

### Run All UI/UX Tests
```bash
npm run test:ui-ux
```

### Run Specific Test Suites

```bash
# Theme integration
npm run test:ui-ux -- --grep "Theme Integration"

# Performance (60fps)
npm run test:ui-ux -- --grep "Performance"

# Device compatibility
npm run test:ui-ux -- --grep "iPhone SE"
npm run test:ui-ux -- --grep "iPhone 14 Pro Max"
npm run test:ui-ux -- --grep "Pixel 5"
npm run test:ui-ux -- --grep "Telegram iOS WebView"

# Keyboard navigation
npm run test:accessibility -- --grep "Keyboard"

# Network throttling
npm run test:ui-ux -- --grep "Network Throttling"

# Visual hierarchy
npm run test:ui-ux -- --grep "Visual Hierarchy"
```

### Run All Accessibility Tests
```bash
npm run test:accessibility
```

```bash
# Accessibility audit (axe-core)
npm run test:accessibility -- --grep "Accessibility Audit"

# Screen reader compatibility
npm run test:accessibility -- --grep "Screen Reader"

# Color contrast
npm run test:accessibility -- --grep "Color Contrast"
```

## Test Coverage

### Theme Integration (T042)
- ✅ Light theme color matching
- ✅ Dark theme color matching
- ✅ Theme-aware chart colors
- ✅ Background color validation

**Validation**: Checks that charts adapt to Telegram's `colorScheme` and `themeParams`.

### Performance (T043)
- ✅ 60fps animation target (55fps+ average, 30fps+ minimum)
- ✅ Page load under 2 seconds
- ✅ FPS measurement during chart interactions
- ✅ No frame drops during date range changes

**Validation**: Uses `requestAnimationFrame` to measure actual FPS during chart animations.

### Device Compatibility (T043a-d)
- ✅ iPhone SE (320x568) - smallest iOS device
- ✅ iPhone 14 Pro Max - Dynamic Island safe areas
- ✅ Android Pixel 5 - Android compatibility
- ✅ Telegram iOS WebView - WebApp API simulation

**Validation**: Uses Playwright device emulation with actual device viewports and user agents.

### Keyboard Navigation (T044b)
- ✅ Tab navigation through interactive elements
- ✅ Focus trap in modal dialogs
- ✅ Logical focus order
- ✅ Visible focus indicators

**Validation**: Simulates Tab key presses and validates focus state.

### Network Throttling (T044c)
- ✅ Loading states under 3G conditions
- ✅ Error handling on network failure
- ✅ 500ms artificial delay simulation
- ✅ Graceful degradation

**Validation**: Uses Playwright route interception to simulate slow/failed networks.

### Accessibility Audit (T044)
- ✅ WCAG 2.0 AA compliance
- ✅ WCAG 2.1 AA compliance
- ✅ Zero axe-core violations
- ✅ All pages validated (feedback, stats, home)

**Validation**: Uses @axe-core/playwright for automated accessibility scanning.

### Screen Reader Compatibility (T044a)
- ✅ ARIA labels on all form inputs
- ✅ Proper semantic roles (button, form, dialog)
- ✅ aria-live for error messages
- ✅ Text alternatives for charts
- ✅ Visible focus indicators
- ✅ Landmark regions (header, main, nav)

**Validation**: Checks for proper ARIA attributes programmatically (simulates screen reader requirements).

### Color Contrast (T045)
- ✅ WCAG AA compliance (4.5:1 for normal text)
- ✅ Button contrast in all states
- ✅ Chart label contrast
- ✅ axe-core color-contrast rule

**Validation**: Uses axe-core's built-in color contrast checking algorithm.

### Visual Hierarchy (T045a)
- ✅ Primary actions visually emphasized (larger font, solid background)
- ✅ Supporting content subdued (smaller font, lower opacity)
- ✅ Proper typography scale
- ✅ Clear visual importance

**Validation**: Checks computed styles (fontSize, fontWeight, backgroundColor) programmatically.

## Performance Budgets

### JavaScript Bundle
- **Target**: < 250KB
- **Test**: Monitors all .js file sizes during page load

### Web Vitals
- **FCP (First Contentful Paint)**: < 1.8s
- **LCP (Largest Contentful Paint)**: < 2.5s
- **Measured via**: Performance API

## Test Data Requirements

### Component Test IDs
The following test IDs must be present in components:

```tsx
// FeedbackForm.tsx
<div data-testid="feedback-form">

// StatsCharts.tsx
<div data-testid="stats-charts">
<button data-testid="date-range-7">  // 7 days
<button data-testid="date-range-30"> // 30 days
<button data-testid="date-range-90"> // 90 days
```

### Mock Data
- **Telegram WebApp API**: Mocked in test setup with `addInitScript()`
- **API Responses**: Intercepted with Playwright's `route()` for controlled testing
- **Network Conditions**: Simulated with route delays and failures

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run UI/UX Validation Tests
  run: npm run test:ui-ux

- name: Run Accessibility Tests
  run: npm run test:accessibility
```

### Pre-commit Hook
```bash
#!/bin/sh
npm run test:ui-ux
npm run test:accessibility
```

## Debugging Tests

### Run with UI Mode
```bash
npm run test:e2e:ui
```

### Run in Headed Mode (see browser)
```bash
npx playwright test tests/e2e/ui-ux-validation.spec.ts --headed
```

### Debug Specific Test
```bash
npx playwright test tests/e2e/accessibility.spec.ts --debug --grep "Color Contrast"
```

### Generate Test Report
```bash
npx playwright test --reporter=html
npx playwright show-report
```

## Troubleshooting

### Test Fails: "Element not found"
- **Cause**: Test ID missing or incorrect
- **Fix**: Add `data-testid` to component, ensure exact match

### Test Fails: "Performance below 60fps"
- **Cause**: Heavy computation or animation
- **Fix**: Optimize chart rendering, use `useMemo`, check for layout thrashing

### Test Fails: "Accessibility violations"
- **Cause**: Missing ARIA labels, poor contrast, invalid HTML
- **Fix**: Run test with `--headed --debug`, inspect violations in console

### Test Fails: "Network timeout"
- **Cause**: Component not loading, API endpoint unreachable
- **Fix**: Check if dev server is running, verify API endpoints

## Writing New Tests

### Template for Device Test
```typescript
test('should work on [Device Name]', async ({ browser }) => {
  const context = await browser.newContext({
    ...devices['Device Name'],
  });
  const page = await context.newPage();

  await page.goto('/your-page');
  await page.waitForSelector('[data-testid="your-component"]');

  // Your assertions here

  await context.close();
});
```

### Template for Accessibility Test
```typescript
test('page should pass axe audit', async ({ page }) => {
  await page.goto('/your-page');
  await page.waitForSelector('[data-testid="your-component"]');

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze();

  expect(results.violations).toHaveLength(0);
});
```

## Success Criteria

All tests must pass for the feature to be considered complete:

- ✅ 0 accessibility violations (axe-core)
- ✅ All device tests pass (iPhone, Android, Telegram)
- ✅ Performance targets met (60fps, < 2s load)
- ✅ Color contrast ratios ≥ 4.5:1 (WCAG AA)
- ✅ Keyboard navigation fully functional
- ✅ Screen reader compatible (proper ARIA)
- ✅ Network resilience validated (3G throttling)
- ✅ Visual hierarchy validated

## References

- [Playwright Documentation](https://playwright.dev/)
- [axe-core Rules](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Telegram WebApp API](https://core.telegram.org/bots/webapps)
- [UI/UX Best Practices Checklist](../../specs/005-mini-app-improvements/checklists/ui-ux-best-practices.md)
