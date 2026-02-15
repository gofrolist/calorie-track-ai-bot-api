import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { handlers } from '@/test/handlers';
import { renderWithProviders } from '@/test/utils';
import MealsPage from '../index';

const server = setupServer(...handlers);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('MealsPage', () => {
  it('renders the meals page title', async () => {
    renderWithProviders(<MealsPage />);
    expect(screen.getByText('Meals')).toBeInTheDocument();
  });

  it('shows empty state when no meals', async () => {
    renderWithProviders(<MealsPage />);
    await waitFor(() => {
      expect(screen.getByText(/no meals/i)).toBeInTheDocument();
    });
  });
});
