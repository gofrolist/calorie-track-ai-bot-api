# End-to-End Testing Guide

## Overview

This guide provides comprehensive E2E testing procedures for the Calorie Track AI Bot Mini App, including happy path scenarios, test scripts, and expected screenshots.

## Test Environment Setup

### Prerequisites
- Node.js 18+ installed
- Backend API running on `http://localhost:8000`
- Telegram Bot configured and running
- Test database with sample data

### Installation
```bash
cd frontend
npm install
npm install --save-dev @playwright/test
npx playwright install
```

### Configuration
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Happy Path Test Scenarios

### Scenario 1: First-Time User Onboarding

#### Test Steps
1. **Launch Mini App**
   - Open Telegram bot
   - Send `/start` command
   - Tap "Open Mini App" button
   - **Expected**: App loads with Today view

2. **View Today Screen**
   - **Expected**: Empty state with "No meals recorded today"
   - **Expected**: Daily summary shows 0 calories
   - **Expected**: Navigation shows Today (active), Stats, Goals

3. **Set Daily Goal**
   - Navigate to Goals tab
   - Tap "Set Daily Goal"
   - Enter "2000" calories
   - Tap "Save"
   - **Expected**: Goal saved successfully
   - **Expected**: Progress bar shows 0%

#### Screenshots
- `screenshots/01-onboarding-today-empty.png`
- `screenshots/02-goals-setup.png`
- `screenshots/03-goal-saved.png`

### Scenario 2: Adding First Meal

#### Test Steps
1. **Add Meal via Bot**
   - Send food photo to bot
   - Wait for AI analysis
   - **Expected**: Bot responds with calorie estimate

2. **View Meal in Mini App**
   - Refresh Mini App
   - Navigate to Today view
   - **Expected**: Meal appears in list
   - **Expected**: Daily summary updates with calories
   - **Expected**: Progress bar shows percentage

3. **Edit Meal Details**
   - Tap on meal item
   - **Expected**: Meal detail page opens
   - **Expected**: Shows calories, macros, meal type
   - Tap "Edit" button
   - Change calories from estimated to actual
   - Tap "Save"
   - **Expected**: Changes saved successfully
   - **Expected**: "Corrected" indicator appears

#### Screenshots
- `screenshots/04-meal-added.png`
- `screenshots/05-meal-detail-view.png`
- `screenshots/06-meal-edited.png`

### Scenario 3: Viewing Statistics

#### Test Steps
1. **Navigate to Stats**
   - Tap "Stats" in navigation
   - **Expected**: Stats page loads
   - **Expected**: Shows "This Week" and "This Month" tabs

2. **View Weekly Data**
   - Ensure "This Week" tab is selected
   - **Expected**: Bar chart shows daily calories
   - **Expected**: Summary shows total and average calories
   - **Expected**: Macros breakdown displayed

3. **View Monthly Data**
   - Tap "This Month" tab
   - **Expected**: Line chart shows daily calories
   - **Expected**: Monthly summary updates
   - **Expected**: Goal progress section visible

#### Screenshots
- `screenshots/07-stats-weekly.png`
- `screenshots/08-stats-monthly.png`
- `screenshots/09-goal-progress.png`

### Scenario 4: Multiple Meals and Progress Tracking

#### Test Steps
1. **Add Multiple Meals**
   - Add breakfast (400 kcal)
   - Add lunch (600 kcal)
   - Add dinner (800 kcal)
   - Add snack (200 kcal)

2. **View Progress**
   - Navigate to Today view
   - **Expected**: All meals listed
   - **Expected**: Total calories = 2000
   - **Expected**: Progress bar at 100%
   - **Expected**: "Goal achieved!" message

3. **Share Progress**
   - Tap share button in daily summary
   - **Expected**: Share dialog opens
   - **Expected**: Share text includes calories and meals

#### Screenshots
- `screenshots/10-multiple-meals.png`
- `screenshots/11-goal-achieved.png`
- `screenshots/12-share-dialog.png`

### Scenario 5: Error Handling

#### Test Steps
1. **Network Error**
   - Disconnect internet
   - Try to refresh data
   - **Expected**: Error message displayed
   - **Expected**: Retry button available

2. **Invalid Input**
   - Go to Goals
   - Try to set goal as "-100"
   - **Expected**: Validation error shown
   - **Expected**: Save button disabled

3. **Meal Not Found**
   - Try to access non-existent meal ID
   - **Expected**: "Meal not found" error
   - **Expected**: Back button to return to Today

#### Screenshots
- `screenshots/13-network-error.png`
- `screenshots/14-validation-error.png`
- `screenshots/15-not-found-error.png`

## Test Implementation

### Base Test Class
```typescript
// tests/e2e/base.test.ts
import { test as base, expect } from '@playwright/test';

export const test = base.extend({
  // Mock Telegram WebApp API
  page: async ({ page }, use) => {
    await page.addInitScript(() => {
      window.Telegram = {
        WebApp: {
          ready: () => {},
          expand: () => {},
          initData: 'test_init_data',
          initDataUnsafe: {
            user: {
              id: 12345,
              first_name: 'Test',
              last_name: 'User',
              username: 'testuser'
            }
          },
          themeParams: {
            bg_color: '#ffffff',
            text_color: '#000000',
            hint_color: '#999999',
            button_color: '#007aff',
            button_text_color: '#ffffff'
          },
          colorScheme: 'light',
          HapticFeedback: {
            impactOccurred: () => {},
            notificationOccurred: () => {}
          },
          showAlert: (message: string) => alert(message)
        }
      };
    });
    await use(page);
  }
});
```

### Today View Tests
```typescript
// tests/e2e/today.spec.ts
import { test, expect } from './base.test';

test.describe('Today View', () => {
  test('displays empty state when no meals', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('h1')).toContainText('Today');
    await expect(page.locator('[data-testid="empty-meals"]')).toBeVisible();
    await expect(page.locator('.progress-bar')).toBeVisible();
  });

  test('displays meals when available', async ({ page }) => {
    // Mock API response with meals
    await page.route('**/api/v1/daily-summary/today', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          meals: [
            {
              id: '1',
              meal_type: 'breakfast',
              kcal_total: 400,
              macros: { protein_g: 20, fat_g: 15, carbs_g: 45 },
              corrected: false,
              created_at: new Date().toISOString()
            }
          ],
          daily_summary: {
            kcal_total: 400,
            macros_totals: { protein_g: 20, fat_g: 15, carbs_g: 45 }
          }
        })
      });
    });

    await page.goto('/');

    await expect(page.locator('[data-testid="meal-item"]')).toHaveCount(1);
    await expect(page.locator('.daily-summary')).toContainText('400 kcal');
  });

  test('navigates to meal detail on click', async ({ page }) => {
    await page.goto('/');
    await page.click('[data-testid="meal-item"]');

    await expect(page).toHaveURL(/\/meal\/\d+/);
    await expect(page.locator('h1')).toContainText('Meal Detail');
  });
});
```

### Goals Tests
```typescript
// tests/e2e/goals.spec.ts
import { test, expect } from './base.test';

test.describe('Goals Page', () => {
  test('allows setting daily goal', async ({ page }) => {
    await page.goto('/goals');

    await page.click('text=Set Daily Goal');
    await page.fill('input[type="number"]', '2000');
    await page.click('text=Save');

    await expect(page.locator('text=Goal updated successfully')).toBeVisible();
    await expect(page.locator('.goal-display')).toContainText('2000 kcal');
  });

  test('validates goal input', async ({ page }) => {
    await page.goto('/goals');

    await page.click('text=Set Daily Goal');
    await page.fill('input[type="number"]', '100');
    await page.click('text=Save');

    await expect(page.locator('.validation-error')).toBeVisible();
    await expect(page.locator('.validation-error')).toContainText('between 500 and 10,000');
  });
});
```

### Stats Tests
```typescript
// tests/e2e/stats.spec.ts
import { test, expect } from './base.test';

test.describe('Stats Page', () => {
  test('displays weekly statistics', async ({ page }) => {
    await page.goto('/stats');

    await expect(page.locator('h1')).toContainText('Week/Month Stats');
    await expect(page.locator('text=This Week')).toBeVisible();
    await expect(page.locator('text=This Month')).toBeVisible();
  });

  test('switches between weekly and monthly views', async ({ page }) => {
    await page.goto('/stats');

    await page.click('text=This Month');
    await expect(page.locator('text=Monthly Summary')).toBeVisible();

    await page.click('text=This Week');
    await expect(page.locator('text=Weekly Summary')).toBeVisible();
  });
});
```

## Screenshot Management

### Screenshot Naming Convention
```
screenshots/
├── 01-onboarding-today-empty.png
├── 02-goals-setup.png
├── 03-goal-saved.png
├── 04-meal-added.png
├── 05-meal-detail-view.png
├── 06-meal-edited.png
├── 07-stats-weekly.png
├── 08-stats-monthly.png
├── 09-goal-progress.png
├── 10-multiple-meals.png
├── 11-goal-achieved.png
├── 12-share-dialog.png
├── 13-network-error.png
├── 14-validation-error.png
└── 15-not-found-error.png
```

### Screenshot Test
```typescript
// tests/e2e/screenshots.spec.ts
import { test, expect } from './base.test';

test.describe('Screenshot Tests', () => {
  test('captures today view with empty state', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Today');
    await page.screenshot({ path: 'screenshots/01-onboarding-today-empty.png' });
  });

  test('captures goals setup flow', async ({ page }) => {
    await page.goto('/goals');
    await page.screenshot({ path: 'screenshots/02-goals-setup.png' });

    await page.click('text=Set Daily Goal');
    await page.screenshot({ path: 'screenshots/03-goal-saved.png' });
  });
});
```

## Running Tests

### Local Development
```bash
# Run all tests
npm run test:e2e

# Run specific test file
npx playwright test tests/e2e/today.spec.ts

# Run with UI mode
npx playwright test --ui

# Generate screenshots
npx playwright test tests/e2e/screenshots.spec.ts
```

### CI/CD Pipeline
```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

## Test Data Management

### Mock Data
```typescript
// tests/fixtures/mock-data.ts
export const mockMeals = [
  {
    id: '1',
    meal_type: 'breakfast',
    kcal_total: 400,
    macros: { protein_g: 20, fat_g: 15, carbs_g: 45 },
    corrected: false,
    created_at: '2024-01-15T08:00:00Z'
  },
  {
    id: '2',
    meal_type: 'lunch',
    kcal_total: 600,
    macros: { protein_g: 30, fat_g: 20, carbs_g: 60 },
    corrected: true,
    created_at: '2024-01-15T13:00:00Z'
  }
];

export const mockDailySummary = {
  kcal_total: 1000,
  macros_totals: { protein_g: 50, fat_g: 35, carbs_g: 105 }
};

export const mockGoal = {
  daily_kcal_target: 2000
};
```

### API Mocking
```typescript
// tests/utils/api-mocks.ts
export const setupApiMocks = (page: Page) => {
  // Mock successful API responses
  page.route('**/api/v1/daily-summary/today', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        meals: mockMeals,
        daily_summary: mockDailySummary
      })
    });
  });

  page.route('**/api/v1/goals', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockGoal)
    });
  });

  // Mock error responses
  page.route('**/api/v1/meals/invalid-id', route => {
    route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Meal not found' })
    });
  });
};
```

## Performance Testing

### Load Time Tests
```typescript
// tests/e2e/performance.spec.ts
import { test, expect } from './base.test';

test.describe('Performance Tests', () => {
  test('page loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForSelector('h1');
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(2000); // 2 seconds max
  });

  test('API responses are fast', async ({ page }) => {
    await page.goto('/');

    const response = await page.waitForResponse('**/api/v1/daily-summary/today');
    expect(response.status()).toBe(200);
    expect(response.request().timing().responseEnd).toBeLessThan(1000);
  });
});
```

## Accessibility Testing

### Keyboard Navigation
```typescript
// tests/e2e/accessibility.spec.ts
import { test, expect } from './base.test';

test.describe('Accessibility Tests', () => {
  test('supports keyboard navigation', async ({ page }) => {
    await page.goto('/');

    // Tab through navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Check focus indicators
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('has proper ARIA labels', async ({ page }) => {
    await page.goto('/');

    const progressBar = page.locator('.progress-bar');
    await expect(progressBar).toHaveAttribute('role', 'progressbar');
    await expect(progressBar).toHaveAttribute('aria-valuenow');
  });
});
```

## Maintenance

### Regular Updates
- Update test data monthly
- Refresh screenshots quarterly
- Review and update test scenarios based on feature changes
- Monitor test execution time and optimize as needed

### Documentation Updates
- Keep test scenarios current with UI changes
- Update screenshot references when UI changes
- Maintain test data consistency
- Document any new test patterns or utilities
