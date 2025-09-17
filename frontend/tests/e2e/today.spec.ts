import { test, expect } from '@playwright/test';

test('today view shows title and empty state', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Today' })).toBeVisible();
  await expect(page.getByText('No meals yet')).toBeVisible();
});
