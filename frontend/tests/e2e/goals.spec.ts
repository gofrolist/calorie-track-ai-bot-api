import { test, expect } from '@playwright/test';

test('goals page shows title and empty state', async ({ page }) => {
  await page.goto('/goals');
  await expect(page.getByRole('heading', { name: 'Goals' })).toBeVisible();
  await expect(page.getByText('No goals set yet.')).toBeVisible();
});
