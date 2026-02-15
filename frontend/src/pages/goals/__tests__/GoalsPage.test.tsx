import { describe, it, expect, beforeAll, afterEach, afterAll } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { handlers } from '@/test/handlers';
import { renderWithProviders } from '@/test/utils';
import GoalsPage from '../index';

const server = setupServer(...handlers);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('GoalsPage', () => {
  it('renders goals title', () => {
    renderWithProviders(<GoalsPage />);
    expect(screen.getByText('Goals')).toBeInTheDocument();
  });

  it('shows current goal after loading', async () => {
    renderWithProviders(<GoalsPage />);
    await waitFor(() => {
      const matches = screen.getAllByText(/2000/);
      expect(matches.length).toBeGreaterThan(0);
    });
  });

  it('has edit button', async () => {
    renderWithProviders(<GoalsPage />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
    });
  });
});
